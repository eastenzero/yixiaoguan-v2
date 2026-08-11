#!/usr/bin/env python3
"""Create a recoverable one-object gap in a green dataset for checkpoint testing."""

import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import weaviate
from weaviate.classes.init import Auth

from app import app
from extensions.ext_database import db
from models.dataset import Dataset, DocumentSegment


parser = argparse.ArgumentParser()
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--artifacts", type=Path, required=True)
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text())
name = next(item for item in manifest["datasets"] if "奖学金-text-v4" in item)
dataset_id = manifest["datasets"][name]["id"]
checkpoint_path = args.artifacts / f"checkpoint-{dataset_id}.json"

endpoint = urlparse(os.environ["WEAVIATE_ENDPOINT"])
grpc_value = os.environ.get("WEAVIATE_GRPC_ENDPOINT", "")
grpc = urlparse(grpc_value if "://" in grpc_value else "grpc://" + grpc_value)
client = weaviate.connect_to_custom(
    http_host=endpoint.hostname or "weaviate",
    http_port=endpoint.port or 8080,
    http_secure=endpoint.scheme == "https",
    grpc_host=grpc.hostname or endpoint.hostname or "weaviate",
    grpc_port=grpc.port or 50051,
    grpc_secure=grpc.scheme == "grpcs",
    auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
    skip_init_checks=True,
)
try:
    with app.app_context():
        dataset = db.session.get(Dataset, dataset_id)
        segment = (
            db.session.query(DocumentSegment)
            .filter_by(dataset_id=dataset_id, enabled=True, status="completed")
            .order_by(DocumentSegment.id)
            .first()
        )
        collection_name = dataset.index_struct_dict["vector_store"]["class_prefix"]
        client.collections.use(collection_name).data.delete_by_id(segment.index_node_id)
        checkpoint = json.loads(checkpoint_path.read_text())
        checkpoint["indexed"] = [item for item in checkpoint["indexed"] if item != segment.index_node_id]
        checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
        marker = {
            "dataset_id": dataset_id,
            "index_node_id": segment.index_node_id,
            "state": "object_and_checkpoint_removed",
        }
        (args.artifacts / "interruption-simulation.json").write_text(
            json.dumps(marker, ensure_ascii=False, indent=2)
        )
        time.sleep(1)
        print("interruption_simulation=READY")
finally:
    client.close()
