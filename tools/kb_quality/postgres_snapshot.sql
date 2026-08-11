-- Read-only Dify knowledge-base snapshot. Each output row is one JSON object.
SELECT jsonb_build_object(
    'record_type', 'dataset',
    'id', d.id,
    'name', d.name,
    'indexing_technique', d.indexing_technique,
    'embedding_model', d.embedding_model,
    'embedding_model_provider', d.embedding_model_provider,
    'index_struct', d.index_struct,
    'retrieval_model', d.retrieval_model,
    'created_at', d.created_at,
    'updated_at', d.updated_at
)::text
FROM datasets d
ORDER BY d.created_at;

SELECT jsonb_build_object(
    'record_type', 'segment',
    'dataset_id', ds.id,
    'dataset_name', ds.name,
    'document_id', doc.id,
    'document_name', doc.name,
    'document_enabled', doc.enabled,
    'document_archived', doc.archived,
    'document_indexing_status', doc.indexing_status,
    'segment_id', seg.id,
    'segment_position', seg.position,
    'content', seg.content,
    'index_node_id', seg.index_node_id,
    'index_node_hash', seg.index_node_hash,
    'segment_enabled', seg.enabled,
    'segment_status', seg.status,
    'segment_error', seg.error,
    'created_at', seg.created_at,
    'updated_at', seg.updated_at
)::text
FROM document_segments seg
JOIN documents doc ON doc.id = seg.document_id
JOIN datasets ds ON ds.id = seg.dataset_id
ORDER BY ds.created_at, doc.position, seg.position;
