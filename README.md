# Achterhus Utilities

A collection of utilities for the `achterhus` home server, packaged as
containerised worker services.

* [Document Router](apps/document-router/README.md) -- Safely organise documents into permanent storage.
* [Photo Router](apps/photo-router/README.md) -- Safely organise JPEG photos into year-based archive folders.

Each application has its own usage instructions and Dockerfile. The images expect
input and destination directories to be mounted inside the container.
