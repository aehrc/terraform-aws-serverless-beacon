## Contents

<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Introduction](#introduction)
- [Data submission schemas](#data-submission-schemas)
- [Model schemas](#model-schemas)
- [Examples](#examples)

<!-- TOC end -->

## Introduction

sBeacon comply with the Beacon V2 schema in terms of the API interface for querying. Data submission to sBeacon follows a similar format with few added fields to build the entity relationships.

## Data submission schemas

* Submit dataset - please follow the JSON schema at [../shared_resources/schemas/submit-dataset-schema-new.json](../shared_resources/schemas/submit-dataset-schema-new.json)
* Update dataset - please follow the JSON schema at [../shared_resources/schemas/submit-dataset-schema-update.json](../shared_resources/schemas/submit-dataset-schema-update.json)

## Model schemas

* Dataset - [../shared_resources/schemas/dataset-schema.json](../shared_resources/schemas/dataset-schema.json)
* Cohort - [../shared_resources/schemas/cohort-schema.json](../shared_resources/schemas/cohort-schema.json)
* Individual - [../shared_resources/schemas/individual-schema.json](../shared_resources/schemas/individual-schema.json)
* Biosample - [../shared_resources/schemas/biosample-schema.json](../shared_resources/schemas/biosample-schema.json)
* Run - [../shared_resources/schemas/run-schema.json](../shared_resources/schemas/run-schema.json)
* Analysis - [../shared_resources/schemas/analysis-schema.json](../shared_resources/schemas/analysis-schema.json)

Schemas does not apply for genomic variations in the ingestion phase of sBeacon. sBeacon supports standard `vcf.gz` files and must be accompanied with their index `vcf.gz.tbi` or `vcf.gz.csi` files.

## Examples

Please refer to [USAGE-GUIDE.md](./USAGE-GUIDE.md) to find a complete example to get started.