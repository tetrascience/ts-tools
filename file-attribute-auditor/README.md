# File Attribute Auditor

The attribute audit notebook is provided as a resource to be used with the [Programmatic auditing of file attributes](https://tetrascience.zendesk.com/hc/en-us/articles/30569863557133-Programmatic-auditing-of-file-attributes) TetraConnect Hub article. The aim of the notebook to provide insight into the following 3 areas:

**Top level review of attribute key names and associated file counts:** this view can be utilized to determine how many files comply with business rules regarding application of file attributes. For example, do all ingested files have critical instrument details associated with them like Instrument Vendor and Instrument Model? 

**Detailed breakdown of attribute key names, associated values and associated file counts:** this view can be utilized to identify fragmentation across file attribute labels. For example, how many files have ThermoFisher Scientific set as Instrument Vendor as opposed to Thermo Fisher Scientific?

**Summary of File-Log Agent scanline file attribute assignments:** this view can be utilized to identify file attribute assignments at the data ingestion source so that new files that are uploaded to the platform with the desired attributes

## How to Use

1. Download file attribute auditor notebook
2. Fill in the connection variables (TDP host name, org slug, user token)
3. Clear example output in notebook that has been provided for reference of expected output
4. Run notebook