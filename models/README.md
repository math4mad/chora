Shared model store. Bytes are git-ignored; every file needs a manifest.json
entry (schemas/manifest.schema.json). Layout follows the ModelScope cache
(`models/models/<org>--<name>/snapshots/<rev>/...`) so benches can point
their `cache_dir` here unmodified.
