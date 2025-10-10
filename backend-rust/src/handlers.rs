use actix_web::{web, HttpResponse, Responder};
use crate::db::DbPool;
use crate::models::{NewAlert, NewVisionEvent, VisionEvent, Alert, DangerZone, NewDangerZone};
use diesel::prelude::*;
use diesel::RunQueryDsl;
use chrono::{NaiveDateTime, Utc, Duration};

pub async fn create_vision_event(
    pool: web::Data<DbPool>,
    item: web::Json<NewVisionEvent>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let insert_result = diesel::insert_into(crate::schema::vision_events::table)
        .values(&item.into_inner())
        .execute(&mut conn);

    match insert_result {
        Ok(_) => {
            // SQLite doesn't return the inserted row, so we query it separately
            let result = crate::schema::vision_events::table
                .order(crate::schema::vision_events::id.desc())
                .select(VisionEvent::as_select())
                .first(&mut conn);
            
            match result {
                Ok(event) => HttpResponse::Created().json(event),
                Err(e) => HttpResponse::InternalServerError().body(format!("Error fetching created event: {}", e)),
            }
        },
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

#[derive(serde::Deserialize)]
pub struct RecentEventsQuery {
    minutes: Option<i64>,
}

pub async fn get_recent_events(
    pool: web::Data<DbPool>,
    query: web::Query<RecentEventsQuery>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");
    let minutes = query.minutes.unwrap_or(10);
    let since = Utc::now().naive_utc() - Duration::minutes(minutes);

    let result = crate::schema::vision_events::table
        .filter(crate::schema::vision_events::ts.ge(since))
        .order(crate::schema::vision_events::ts.desc())
        .select(VisionEvent::as_select())
        .load(&mut conn);

    match result {
        Ok(events) => HttpResponse::Ok().json(events),
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

pub async fn create_alert(
    pool: web::Data<DbPool>,
    item: web::Json<NewAlert>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let insert_result = diesel::insert_into(crate::schema::alerts::table)
        .values(&item.into_inner())
        .execute(&mut conn);

    match insert_result {
        Ok(_) => {
            let result = crate::schema::alerts::table
                .order(crate::schema::alerts::id.desc())
                .select(Alert::as_select())
                .first(&mut conn);
            
            match result {
                Ok(alert) => HttpResponse::Created().json(alert),
                Err(e) => HttpResponse::InternalServerError().body(format!("Error fetching created alert: {}", e)),
            }
        },
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

pub async fn get_recent_alerts(
    pool: web::Data<DbPool>,
    query: web::Query<RecentEventsQuery>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");
    let minutes = query.minutes.unwrap_or(60);
    let since = Utc::now().naive_utc() - Duration::minutes(minutes);

    let result = crate::schema::alerts::table
        .filter(crate::schema::alerts::ts.ge(since))
        .order(crate::schema::alerts::ts.desc())
        .select(Alert::as_select())
        .load(&mut conn);

    match result {
        Ok(alerts) => HttpResponse::Ok().json(alerts),
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}


pub async fn create_danger_zone(
    pool: web::Data<DbPool>,
    item: web::Json<NewDangerZone>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let insert_result = diesel::insert_into(crate::schema::danger_zones::table)
        .values(&item.into_inner())
        .execute(&mut conn);

    match insert_result {
        Ok(_) => {
            let result = crate::schema::danger_zones::table
                .order(crate::schema::danger_zones::id.desc())
                .select(DangerZone::as_select())
                .first(&mut conn);
            
            match result {
                Ok(zone) => HttpResponse::Created().json(zone),
                Err(e) => HttpResponse::InternalServerError().body(format!("Error fetching created zone: {}", e)),
            }
        },
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

pub async fn get_danger_zones(
    pool: web::Data<DbPool>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let result = crate::schema::danger_zones::table
        .select(DangerZone::as_select())
        .load(&mut conn);

    match result {
        Ok(zones) => HttpResponse::Ok().json(zones),
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

pub async fn update_danger_zone(
    pool: web::Data<DbPool>,
    path: web::Path<i32>,
    item: web::Json<NewDangerZone>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");
    let zone_id = path.into_inner();

    let update_result = diesel::update(crate::schema::danger_zones::table.find(zone_id))
        .set(item.into_inner())
        .execute(&mut conn);

    match update_result {
        Ok(_) => {
            let result = crate::schema::danger_zones::table
                .find(zone_id)
                .select(DangerZone::as_select())
                .first(&mut conn);

            match result {
                Ok(zone) => HttpResponse::Ok().json(zone),
                Err(e) => HttpResponse::InternalServerError().body(format!("Error fetching updated zone: {}", e)),
            }
        },
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

pub async fn delete_danger_zone(
    pool: web::Data<DbPool>,
    path: web::Path<i32>,
) -> impl Responder {
    let mut conn = pool.get().expect("couldn't get db connection from pool");
    let zone_id = path.into_inner();

    let result = diesel::delete(crate::schema::danger_zones::table.find(zone_id))
        .execute(&mut conn);

    match result {
        Ok(_) => HttpResponse::Ok().finish(),
        Err(e) => HttpResponse::InternalServerError().body(e.to_string()),
    }
}

pub fn init_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .service(
                web::scope("/events")
                    .route("/vision", web::post().to(create_vision_event))
                    .route("/recent", web::get().to(get_recent_events))
            )
            .service(
                web::scope("/alerts")
                    .route("", web::post().to(create_alert))
                    .route("/recent", web::get().to(get_recent_alerts))
            )
            .service(
                web::scope("/zones")
                    .route("", web::post().to(create_danger_zone))
                    .route("", web::get().to(get_danger_zones))
                    .route("/{id}", web::put().to(update_danger_zone))
                    .route("/{id}", web::delete().to(delete_danger_zone))
            )
    );
}
