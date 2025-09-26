#!/bin/bash

# 数据备份和恢复脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"
BACKUP_DIR="$PROJECT_DIR/backups"
CONFIG_FILE="$PROJECT_DIR/.env"

# 配置参数
BACKUP_RETENTION_DAYS=30
COMPRESSION_LEVEL=6
ENCRYPTION_ENABLED=false
ENCRYPTION_KEY=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    local deps=("tar" "gzip")
    
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        deps+=("openssl")
    fi
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "缺少依赖: $dep"
            exit 1
        fi
    done
    
    log_success "依赖检查完成"
}

# 创建备份目录
create_backup_dir() {
    local timestamp=$1
    local backup_path="$BACKUP_DIR/$timestamp"
    
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# 备份数据库
backup_database() {
    local backup_path=$1
    local db_file="$DATA_DIR/baby_safety.db"
    
    if [ -f "$db_file" ]; then
        log_info "备份数据库..."
        
        # 停止相关服务以确保数据一致性
        if command -v docker-compose &> /dev/null; then
            log_info "停止服务以确保数据一致性..."
            docker-compose -f "$PROJECT_DIR/docker-compose.yml" stop backend-go || true
        fi
        
        # 复制数据库文件
        cp "$db_file" "$backup_path/baby_safety.db"
        
        # 重启服务
        if command -v docker-compose &> /dev/null; then
            log_info "重启服务..."
            docker-compose -f "$PROJECT_DIR/docker-compose.yml" start backend-go || true
        fi
        
        log_success "数据库备份完成"
    else
        log_warning "数据库文件不存在: $db_file"
    fi
}

# 备份配置文件
backup_config() {
    local backup_path=$1
    
    log_info "备份配置文件..."
    
    local config_files=(
        ".env"
        "docker-compose.yml"
        "docker-compose.prod.yml"
        "monitoring/prometheus.yml"
        "monitoring/alerts.yml"
    )
    
    mkdir -p "$backup_path/config"
    
    for config in "${config_files[@]}"; do
        local full_path="$PROJECT_DIR/$config"
        if [ -f "$full_path" ]; then
            cp "$full_path" "$backup_path/config/"
            log_info "备份配置: $config"
        fi
    done
    
    log_success "配置文件备份完成"
}

# 备份日志文件
backup_logs() {
    local backup_path=$1
    local logs_dir="$PROJECT_DIR/logs"
    
    if [ -d "$logs_dir" ]; then
        log_info "备份日志文件..."
        
        # 只备份最近7天的日志
        mkdir -p "$backup_path/logs"
        find "$logs_dir" -name "*.log" -mtime -7 -exec cp {} "$backup_path/logs/" \;
        
        log_success "日志文件备份完成"
    else
        log_warning "日志目录不存在: $logs_dir"
    fi
}

# 备份模型文件
backup_models() {
    local backup_path=$1
    local models_dir="$DATA_DIR/models"
    
    if [ -d "$models_dir" ]; then
        log_info "备份模型文件..."
        
        mkdir -p "$backup_path/models"
        cp -r "$models_dir"/* "$backup_path/models/" 2>/dev/null || true
        
        log_success "模型文件备份完成"
    else
        log_warning "模型目录不存在: $models_dir"
    fi
}

# 创建备份信息文件
create_backup_info() {
    local backup_path=$1
    local timestamp=$2
    
    cat > "$backup_path/backup_info.json" << EOF
{
    "timestamp": "$timestamp",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "user": "$(whoami)",
    "project_dir": "$PROJECT_DIR",
    "git_commit": "$(cd "$PROJECT_DIR" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null || echo 'unknown')",
    "backup_size": "$(du -sh "$backup_path" | cut -f1)",
    "files_count": $(find "$backup_path" -type f | wc -l)
}
EOF
}

# 压缩备份
compress_backup() {
    local backup_path=$1
    local timestamp=$2
    
    log_info "压缩备份文件..."
    
    local archive_name="backup_${timestamp}.tar.gz"
    local archive_path="$BACKUP_DIR/$archive_name"
    
    # 创建压缩包
    tar -czf "$archive_path" -C "$BACKUP_DIR" "$timestamp"
    
    # 删除原始目录
    rm -rf "$backup_path"
    
    log_success "备份已压缩: $archive_path"
    echo "$archive_path"
}

# 加密备份
encrypt_backup() {
    local archive_path=$1
    
    if [ "$ENCRYPTION_ENABLED" != "true" ] || [ -z "$ENCRYPTION_KEY" ]; then
        echo "$archive_path"
        return
    fi
    
    log_info "加密备份文件..."
    
    local encrypted_path="${archive_path}.enc"
    
    openssl enc -aes-256-cbc -salt -in "$archive_path" -out "$encrypted_path" -k "$ENCRYPTION_KEY"
    
    # 删除未加密的文件
    rm "$archive_path"
    
    log_success "备份已加密: $encrypted_path"
    echo "$encrypted_path"
}

# 执行完整备份
create_backup() {
    log_info "开始创建备份..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path=$(create_backup_dir "$timestamp")
    
    # 备份各个组件
    backup_database "$backup_path"
    backup_config "$backup_path"
    backup_logs "$backup_path"
    backup_models "$backup_path"
    
    # 创建备份信息
    create_backup_info "$backup_path" "$timestamp"
    
    # 压缩备份
    local archive_path=$(compress_backup "$backup_path" "$timestamp")
    
    # 加密备份（如果启用）
    local final_path=$(encrypt_backup "$archive_path")
    
    log_success "备份创建完成: $final_path"
    
    # 清理旧备份
    cleanup_old_backups
    
    echo "$final_path"
}

# 解密备份
decrypt_backup() {
    local encrypted_path=$1
    
    if [[ ! "$encrypted_path" =~ \.enc$ ]]; then
        echo "$encrypted_path"
        return
    fi
    
    if [ -z "$ENCRYPTION_KEY" ]; then
        log_error "需要提供解密密钥"
        exit 1
    fi
    
    log_info "解密备份文件..."
    
    local decrypted_path="${encrypted_path%.enc}"
    
    openssl enc -aes-256-cbc -d -in "$encrypted_path" -out "$decrypted_path" -k "$ENCRYPTION_KEY"
    
    log_success "备份已解密: $decrypted_path"
    echo "$decrypted_path"
}

# 解压备份
extract_backup() {
    local archive_path=$1
    local extract_to=${2:-"$BACKUP_DIR/restore_$(date +%Y%m%d_%H%M%S)"}
    
    log_info "解压备份文件..."
    
    mkdir -p "$extract_to"
    tar -xzf "$archive_path" -C "$extract_to" --strip-components=1
    
    log_success "备份已解压到: $extract_to"
    echo "$extract_to"
}

# 恢复数据库
restore_database() {
    local restore_path=$1
    local db_backup="$restore_path/baby_safety.db"
    
    if [ ! -f "$db_backup" ]; then
        log_error "备份中未找到数据库文件"
        return 1
    fi
    
    log_info "恢复数据库..."
    
    # 停止服务
    if command -v docker-compose &> /dev/null; then
        log_info "停止服务..."
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" stop backend-go || true
    fi
    
    # 备份当前数据库
    if [ -f "$DATA_DIR/baby_safety.db" ]; then
        cp "$DATA_DIR/baby_safety.db" "$DATA_DIR/baby_safety.db.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 恢复数据库
    mkdir -p "$DATA_DIR"
    cp "$db_backup" "$DATA_DIR/baby_safety.db"
    
    # 重启服务
    if command -v docker-compose &> /dev/null; then
        log_info "重启服务..."
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" start backend-go || true
    fi
    
    log_success "数据库恢复完成"
}

# 恢复配置文件
restore_config() {
    local restore_path=$1
    local config_backup_dir="$restore_path/config"
    
    if [ ! -d "$config_backup_dir" ]; then
        log_warning "备份中未找到配置文件"
        return
    fi
    
    log_info "恢复配置文件..."
    
    # 备份当前配置
    local current_backup_dir="$PROJECT_DIR/config_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$current_backup_dir"
    
    for config in .env docker-compose.yml docker-compose.prod.yml; do
        if [ -f "$PROJECT_DIR/$config" ]; then
            cp "$PROJECT_DIR/$config" "$current_backup_dir/"
        fi
    done
    
    # 恢复配置
    cp -r "$config_backup_dir"/* "$PROJECT_DIR/"
    
    log_success "配置文件恢复完成"
    log_info "原配置已备份到: $current_backup_dir"
}

# 执行恢复
restore_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_info "开始恢复备份: $backup_file"
    
    # 解密（如果需要）
    local decrypted_path=$(decrypt_backup "$backup_file")
    
    # 解压
    local restore_path=$(extract_backup "$decrypted_path")
    
    # 显示备份信息
    if [ -f "$restore_path/backup_info.json" ]; then
        log_info "备份信息:"
        cat "$restore_path/backup_info.json" | jq . 2>/dev/null || cat "$restore_path/backup_info.json"
    fi
    
    # 确认恢复
    read -p "确认要恢复此备份吗？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "恢复已取消"
        rm -rf "$restore_path"
        exit 0
    fi
    
    # 执行恢复
    restore_database "$restore_path"
    restore_config "$restore_path"
    
    # 清理
    rm -rf "$restore_path"
    
    log_success "备份恢复完成"
}

# 列出备份
list_backups() {
    log_info "可用备份列表:"
    echo "================================"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warning "备份目录不存在"
        return
    fi
    
    local backups=($(find "$BACKUP_DIR" -name "backup_*.tar.gz*" -type f | sort -r))
    
    if [ ${#backups[@]} -eq 0 ]; then
        log_warning "未找到备份文件"
        return
    fi
    
    for i in "${!backups[@]}"; do
        local backup="${backups[$i]}"
        local filename=$(basename "$backup")
        local size=$(du -sh "$backup" | cut -f1)
        local date=$(stat -f%Sm -t"%Y-%m-%d %H:%M:%S" "$backup" 2>/dev/null || stat -c%y "$backup" 2>/dev/null | cut -d. -f1)
        
        printf "%2d. %-30s %8s %s\n" $((i+1)) "$filename" "$size" "$date"
    done
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        return
    fi
    
    # 删除超过保留期的备份
    find "$BACKUP_DIR" -name "backup_*.tar.gz*" -mtime +$BACKUP_RETENTION_DAYS -delete
    
    local remaining=$(find "$BACKUP_DIR" -name "backup_*.tar.gz*" | wc -l)
    log_success "清理完成，剩余 $remaining 个备份文件"
}

# 验证备份
verify_backup() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        return 1
    fi
    
    log_info "验证备份文件: $backup_file"
    
    # 检查文件完整性
    if [[ "$backup_file" =~ \.enc$ ]]; then
        log_info "检测到加密文件，需要解密验证"
        if [ -z "$ENCRYPTION_KEY" ]; then
            log_error "需要提供解密密钥"
            return 1
        fi
        # 这里可以添加加密文件的验证逻辑
    else
        # 验证tar文件
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            log_success "备份文件验证通过"
            
            # 显示内容列表
            log_info "备份内容:"
            tar -tzf "$backup_file" | head -20
            local total_files=$(tar -tzf "$backup_file" | wc -l)
            if [ $total_files -gt 20 ]; then
                echo "... 和其他 $((total_files - 20)) 个文件"
            fi
        else
            log_error "备份文件损坏或格式错误"
            return 1
        fi
    fi
}

# 主函数
main() {
    case "${1:-help}" in
        "backup"|"create")
            check_dependencies
            create_backup
            ;;
        "restore")
            if [ -z "$2" ]; then
                log_error "请指定要恢复的备份文件"
                list_backups
                exit 1
            fi
            check_dependencies
            restore_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "verify")
            if [ -z "$2" ]; then
                log_error "请指定要验证的备份文件"
                exit 1
            fi
            verify_backup "$2"
            ;;
        "help"|*)
            echo "婴儿安全监控系统数据备份工具"
            echo ""
            echo "用法: $0 <command> [options]"
            echo ""
            echo "命令:"
            echo "  backup, create    创建新备份"
            echo "  restore <file>    恢复指定备份"
            echo "  list             列出所有备份"
            echo "  cleanup          清理旧备份"
            echo "  verify <file>    验证备份文件"
            echo "  help             显示此帮助信息"
            echo ""
            echo "环境变量:"
            echo "  ENCRYPTION_KEY   备份加密密钥"
            echo "  BACKUP_RETENTION_DAYS  备份保留天数 (默认: 30)"
            ;;
    esac
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行主函数
main "$@"