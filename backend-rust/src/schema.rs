// @generated automatically by Diesel CLI.

diesel::table! {
    alerts (id) {
        id -> Integer,
        ts -> Timestamp,
        level -> Text,
        reason -> Nullable<Text>,
        track_id -> Nullable<Text>,
        details -> Nullable<Text>,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::table! {
    danger_zones (id) {
        id -> Integer,
        name -> Text,
        polygon_json -> Text,
        level -> Text,
        enabled -> Bool,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::table! {
    vision_events (id) {
        id -> Integer,
        ts -> Timestamp,
        track_id -> Text,
        x -> Integer,
        y -> Integer,
        w -> Integer,
        h -> Integer,
        action -> Nullable<Text>,
        risk_score -> Nullable<Float>,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::allow_tables_to_appear_in_same_query!(alerts, danger_zones, vision_events,);
