# tap-bitso

⚠️ Warning: this project is under active development, essential features are still missing and implementation subject to change. ⚠️

`tap-bitso` is a Singer tap for the [Bitso API](https://bitso.com/api_info).

Built with the Meltano [SDK](https://gitlab.com/meltano/sdk) for Singer Taps.

## Installation

```bash
pipx install git+https://github.com/edgarrmondragon/tap-bitso.git
```

## Configuration

### Accepted Config Options

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-bitso --about
```

| Field      | Description             | Type           | Required | Default                 |
|------------|-------------------------|----------------|----------|-------------------------|
| `key`      | Bitso API Key           | `string`       | yes      |                         |
| `secret`   | Bitso API Secret        | `string`       | yes      |                         |
| `base_url` | Bitso API URL           | `string`       | no       | `https://api.bitso.com` |
| `books`    | Tickers to get data for | `list(string)` | no       | `["btc_mxn"]`           |

### Source Authentication and Authorization

This tap handles the [digest access authentication for the Bitso API](https://docs.bitso.com/bitso-api/docs/authentication).

## Usage

You can easily run `tap-bitso` by itself or in a pipeline using [Meltano](www.meltano.com).

### Executing the Tap Directly

```bash
tap-bitso --version
tap-bitso --help
tap-bitso --config CONFIG --discover > ./catalog.json
```

## Developer Resources

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

<!--
### Create and Run Tests

Create tests within the `tap_bitso/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-bitso` CLI interface directly using `poetry run`:

```bash
poetry run tap-bitso --help
```
-->

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-bitso
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-bitso --version
# OR run a test `elt` pipeline:
meltano elt tap-bitso target-sqlite
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.
