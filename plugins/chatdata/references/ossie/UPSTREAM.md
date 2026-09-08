# Bundled Apache Ossie schema

ChatData bundles the Apache Ossie core JSON Schema so local validation works
without a network connection.

- Upstream: https://github.com/apache/ossie
- Commit: `89bb502bf8e00567c58c439f573bb869a3621a90`
- Source: `core-spec/ossie-schema.json`
- Specification version: `0.2.0.dev0` (draft)
- SHA-256: `ce3f3e4a7098f53beb92136cc4cf2f107dde799815497e02a76af4bdf29d2716`

`ossie-schema.json`, `LICENSE`, and `NOTICE` are copied without modification
from that commit. Apache Ossie was formerly named Open Semantic Interchange.

ChatData's dependency-free runtime validator supports the fixed JSON Schema
vocabulary used by this pinned file. It is not a general-purpose JSON Schema
validator and does not claim compatibility with every Ossie consumer.
