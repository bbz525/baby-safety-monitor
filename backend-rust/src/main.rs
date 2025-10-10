#[macro_use]
extern crate diesel;

use actix_web::{App, HttpServer, web};
use actix_cors::Cors;

mod db;
mod models;
mod schema;
mod handlers;
mod sse;

use sse::Broadcaster;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenvy::dotenv().ok();
    env_logger::init_from_env(env_logger::Env::new().default_filter_or("info"));

    let pool = db::establish_connection();
    let broadcaster = Broadcaster::new();

    log::info!("Starting server at http://127.0.0.1:8080");

    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);

        App::new()
            .app_data(web::Data::new(pool.clone()))
            .app_data(web::Data::new(broadcaster.clone()))
            .wrap(cors)
            .configure(handlers::init_routes)
            .route("/stream", web::get().to(sse::sse_stream))
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
