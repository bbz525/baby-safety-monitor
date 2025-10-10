use actix_web::{web, Error, HttpResponse};
use actix_web_actors::ws;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::time::interval;
use bytes::Bytes;
use futures::Stream;

use crate::models::{VisionEvent, Alert};

const HEARTBEAT_INTERVAL: Duration = Duration::from_secs(5);
const CLIENT_TIMEOUT: Duration = Duration::from_secs(10);

#[derive(Debug, Clone)]
pub struct Broadcaster {
    clients: Arc<Mutex<Vec<ws::WebsocketContext<SseSession>>>>,
}

impl Broadcaster {
    pub fn new() -> Self {
        Broadcaster {
            clients: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn new_client(&self, ctx: ws::WebsocketContext<SseSession>) {
        self.clients.lock().unwrap().push(ctx);
    }

    pub fn send_event(&self, event: &str, data: &str) {
        let msg = format!("event: {}\ndata: {}\n\n", event, data);
        for client in self.clients.lock().unwrap().iter() {
            client.text(msg.clone());
        }
    }
}

pub struct SseSession {
    hb: Instant,
    broadcaster: Broadcaster,
}

impl SseSession {
    pub fn new(broadcaster: Broadcaster) -> SseSession {
        SseSession {
            hb: Instant::now(),
            broadcaster,
        }
    }

    fn hb(&self, ctx: &mut ws::WebsocketContext<Self>) {
        ctx.run_interval(HEARTBEAT_INTERVAL, |act, ctx| {
            if Instant::now().duration_since(act.hb) > CLIENT_TIMEOUT {
                println!("Client timed out");
                ctx.stop();
                return;
            }
            ctx.text("event: heartbeat\ndata: {}\n\n");
        });
    }
}

impl Stream for SseSession {
    type Item = Result<Bytes, Error>;

    fn poll_next(
        self: std::pin::Pin<&mut Self>,
        _cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Option<Self::Item>> {
        std::task::Poll::Pending
    }
}

impl ws::Actor for SseSession {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        self.hb(ctx);
        self.broadcaster.new_client(ctx.address());
    }
}

impl ws::StreamHandler<Result<ws::Message, ws::ProtocolError>> for SseSession {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                self.hb = Instant::now();
                ctx.pong(&msg);
            }
            Ok(ws::Message::Pong(_)) => {
                self.hb = Instant::now();
            }
            Ok(ws::Message::Close(reason)) => {
                ctx.close(reason);
                ctx.stop();
            }
            _ => (),
        }
    }
}

pub async fn sse_stream(broadcaster: web::Data<Broadcaster>) -> impl Responder {
    let session = SseSession::new(broadcaster.get_ref().clone());
    let resp = HttpResponse::Ok()
        .content_type("text/event-stream")
        .streaming(session);
    resp
}
