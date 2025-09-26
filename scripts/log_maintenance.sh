#!/bin/bash

# 日志轮转和清理脚本

set -e

LOG_DIR="/app/logs"
MAX_SIZE="100M"
MAX_AGE_DAYS=30
BACKUP_COUNT=10

echo "🗂️  开始日志维护..."

# 创建日志目录
mkdir -p $LOG_DIR/{backend,frontend,vision,agent}

# 轮转函数
rotate_logs() {
    local service=$1
    local log_file="$LOG_DIR/$service/$service.log"
    
    if [ -f "$log_file" ]; then
        # 检查文件大小
        size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo 0)
        max_bytes=$((100 * 1024 * 1024))  # 100MB
        
        if [ $size -gt $max_bytes ]; then
            echo "📦 轮转 $service 日志文件..."
            
            # 移动现有备份
            for i in $(seq $((BACKUP_COUNT-1)) -1 1); do
                if [ -f "$log_file.$i" ]; then
                    mv "$log_file.$i" "$log_file.$((i+1))"
                fi
            done
            
            # 轮转当前日志
            mv "$log_file" "$log_file.1"
            
            # 压缩旧日志
            if [ -f "$log_file.1" ]; then
                gzip "$log_file.1"
                mv "$log_file.1.gz" "$log_file.1.gz"
            fi
            
            # 重新创建日志文件
            touch "$log_file"
            chmod 644 "$log_file"
        fi
    fi
}

# 清理旧日志
cleanup_old_logs() {
    local service=$1
    local service_dir="$LOG_DIR/$service"
    
    if [ -d "$service_dir" ]; then
        echo "🧹 清理 $service 旧日志文件..."
        
        # 删除超过指定天数的日志文件
        find "$service_dir" -name "*.log.*" -mtime +$MAX_AGE_DAYS -delete
        find "$service_dir" -name "*.gz" -mtime +$MAX_AGE_DAYS -delete
        
        # 删除超过备份数量的文件
        ls -t "$service_dir"/*.log.*.gz 2>/dev/null | tail -n +$((BACKUP_COUNT+1)) | xargs rm -f
    fi
}

# 处理各个服务的日志
for service in backend frontend vision agent; do
    rotate_logs $service
    cleanup_old_logs $service
done

# 生成日志统计报告
generate_log_report() {
    echo "📊 生成日志统计报告..."
    
    report_file="$LOG_DIR/log_report_$(date +%Y%m%d).txt"
    
    cat > "$report_file" << EOF
婴儿安全监控系统日志报告
生成时间: $(date)
==================================

磁盘使用情况:
$(du -sh $LOG_DIR/*)

各服务日志文件数量:
EOF
    
    for service in backend frontend vision agent; do
        service_dir="$LOG_DIR/$service"
        if [ -d "$service_dir" ]; then
            count=$(find "$service_dir" -name "*.log*" | wc -l)
            echo "$service: $count 个文件" >> "$report_file"
        fi
    done
    
    echo "" >> "$report_file"
    echo "最近错误日志摘要:" >> "$report_file"
    
    # 提取最近的错误日志
    for service in backend frontend vision agent; do
        log_file="$LOG_DIR/$service/$service.log"
        if [ -f "$log_file" ]; then
            echo "" >> "$report_file"
            echo "=== $service 错误 ===" >> "$report_file"
            grep -i "error\|exception\|failed" "$log_file" | tail -5 >> "$report_file" || echo "无错误日志" >> "$report_file"
        fi
    done
    
    echo "✅ 日志报告生成完成: $report_file"
}

# 日志压缩优化
optimize_logs() {
    echo "🗜️  优化日志存储..."
    
    # 查找未压缩的旧日志并压缩
    find $LOG_DIR -name "*.log.*" -not -name "*.gz" -mtime +1 -exec gzip {} \;
    
    # 合并小的日志文件
    for service in backend frontend vision agent; do
        service_dir="$LOG_DIR/$service"
        if [ -d "$service_dir" ]; then
            # 查找小于1MB的压缩文件，合并它们
            small_files=$(find "$service_dir" -name "*.gz" -size -1M | sort)
            if [ ! -z "$small_files" ] && [ $(echo "$small_files" | wc -l) -gt 3 ]; then
                echo "🔗 合并 $service 的小日志文件..."
                archive_name="$service_dir/merged_$(date +%Y%m%d_%H%M%S).log.gz"
                zcat $small_files | gzip > "$archive_name"
                echo "$small_files" | xargs rm -f
            fi
        fi
    done
}

# 设置日志监控
setup_log_monitoring() {
    echo "👀 设置日志监控..."
    
    # 创建日志监控脚本
    cat > "$LOG_DIR/monitor_logs.sh" << 'EOF'
#!/bin/bash

# 实时监控关键日志

ALERT_KEYWORDS="FATAL|CRITICAL|OutOfMemory|Connection refused"
LOG_FILES="/app/logs/*/*.log"

tail -f $LOG_FILES | while read line; do
    if echo "$line" | grep -qE "$ALERT_KEYWORDS"; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "[$timestamp] 🚨 ALERT: $line" | tee -a "/app/logs/alerts.log"
        
        # 可以在这里添加钉钉通知或其他告警机制
        # curl -X POST "$DINGTALK_WEBHOOK" -d "..."
    fi
done
EOF
    
    chmod +x "$LOG_DIR/monitor_logs.sh"
}

# 执行所有维护任务
generate_log_report
optimize_logs
setup_log_monitoring

echo "✨ 日志维护完成！"
echo "📁 日志目录: $LOG_DIR"
echo "📊 日志报告: $LOG_DIR/log_report_$(date +%Y%m%d).txt"
echo "👀 启动日志监控: $LOG_DIR/monitor_logs.sh &"