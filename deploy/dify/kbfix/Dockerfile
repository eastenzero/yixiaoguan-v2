ARG BASE_IMAGE=langgenius/dify-api@sha256:d1c73b3be4ba3212d4119c77e15230215e8bcf760ed64f80cfea121c277e1108
FROM ${BASE_IMAGE}

ARG BUILD_TIMESTAMP
ARG PATCH_SHA256
LABEL org.opencontainers.image.title="Dify API 1.13.3 kbfix"
LABEL org.opencontainers.image.description="Use document_segments.index_node_id as the Weaviate object UUID"
LABEL org.opencontainers.image.base.digest="sha256:d1c73b3be4ba3212d4119c77e15230215e8bcf760ed64f80cfea121c277e1108"
LABEL io.yixiaoguan.kbfix.patch.sha256="${PATCH_SHA256}"
LABEL io.yixiaoguan.kbfix.built-at="${BUILD_TIMESTAMP}"

USER root
COPY apply_weaviate_identity_patch.py /tmp/apply_weaviate_identity_patch.py
RUN python /tmp/apply_weaviate_identity_patch.py \
    && rm /tmp/apply_weaviate_identity_patch.py
