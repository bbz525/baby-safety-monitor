use actix_web::{web, HttpResponse, Responder};
use std::sync::{Arc, Mutex};
use bytes::Bytes;
use futures::StreamExt;
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;

#[derive(Debug, Clone)]
pub struct Broadcaster {
    senders: Arc<Mutex<Vec<mpsc::Sender<String>>>>,
}

impl Broadcaster {
    pub fn new() -> Self {
        Broadcaster {
            senders: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn new_client(&self) -> mpsc::Receiver<String> {
        let (tx, rx) = mpsc::channel(100);
        self.senders.lock().unwrap().push(tx);
        rx
    }

    pub fn send_event(&self, event: &str, data: &str) {
        let msg = format!("event: {}\ndata: {}\n\n", event, data);
        let mut senders = self.senders.lock().unwrap();
        senders.retain(|tx| tx.try_send(msg.clone()).is_ok());
    }
}

pub async fn sse_stream(broadcaster: web::Data<Broadcaster>) -> impl Responder {
    let rx = broadcaster.new_client();
    let stream = ReceiverStream::new(rx).map(|msg| Ok::<Bytes, actix_web::Error>(Bytes::from(msg)));

    HttpResponse::Ok()
        .content_type("text/event-stream")
        .streaming(stream)
}
