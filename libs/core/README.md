# Core

`core` is a local library shared by the worker applications. It currently
provides the `telemetry_context` context manager, which creates an
`achterhus-telemetry-client` client when `SERVICE_RUN_ID` is set and otherwise
disables telemetry.

The library requires Python 3.14 or newer.

The application projects consume this package through a relative local path
dependency. Each application lockfile therefore resolves the library and its
dependencies independently with that application.
