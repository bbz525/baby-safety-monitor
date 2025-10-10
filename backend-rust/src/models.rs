use crate::schema::{alerts, danger_zones, vision_events};
use chrono::NaiveDateTime;
use diesel::prelude::*;
use serde::{Deserialize, Serialize};

// VisionEvent Model
#[derive(Queryable, Selectable, Serialize, Deserialize, Debug)]
#[diesel(table_name = vision_events)]
pub struct VisionEvent {
    pub id: i32,
    pub ts: NaiveDateTime,
    pub track_id: String,
    pub x: i32,
    pub y: i32,
    pub w: i32,
    pub h: i32,
    pub action: Option<String>,
    pub risk_score: Option<f32>,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}

#[derive(Insertable, Deserialize)]
#[diesel(table_name = vision_events)]
pub struct NewVisionEvent {
    pub ts: NaiveDateTime,
    pub track_id: String,
    pub x: i32,
    pub y: i32,
    pub w: i32,
    pub h: i32,
    pub action: Option<String>,
    pub risk_score: Option<f32>,
}

// Alert Model
#[derive(Queryable, Selectable, Serialize, Deserialize, Debug)]
#[diesel(table_name = alerts)]
pub struct Alert {
    pub id: i32,
    pub ts: NaiveDateTime,
    pub level: String,
    pub reason: Option<String>,
    pub track_id: Option<String>,
    pub details: Option<String>,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}

#[derive(Insertable, Deserialize)]
#[diesel(table_name = alerts)]
pub struct NewAlert {
    pub ts: NaiveDateTime,
    pub level: String,
    pub reason: Option<String>,
    pub track_id: Option<String>,
    pub details: Option<String>,
}

// DangerZone Model
#[derive(Queryable, Selectable, Serialize, Deserialize, Debug)]
#[diesel(table_name = danger_zones)]
pub struct DangerZone {
    pub id: i32,
    pub name: String,
    pub polygon_json: String,
    pub level: String,
    pub enabled: bool,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}

#[derive(Insertable, AsChangeset, Deserialize)]
#[diesel(table_name = danger_zones)]
pub struct NewDangerZone {
    pub name: String,
    pub polygon_json: String,
    pub level: String,
    pub enabled: bool,
}
