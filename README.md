**This folder contains:**
- Excel-based LCA-tool for urban transport modes by ITF (2020)
- CSV-file of GHG emissions per passenger-kilometer by transport modes

# LCA tool for urban transport modes

The International Transport Forum (ITF) has developed a comprehensive life-cycle analysis Excel-based tool of urban transport modes including the new mobility services, such as shared vehicles and ridesourcing. The Excel file includes calculations and assumptions made for the ITF report titled as "Good to go? Assessing the environmental performance of new mobility in cities".

## How to use?

The Excel file consist of multiple sheets with color-coded tabs. 
- **The sheet tabs in blue**, depict different stages of the life-cycle (e.g. manufacturing, use, operation) and includes the key inputs and calculations for the assessments. 
- **The sheet tabs in grey**, contain assumptions and references of the data sources for every transport mode, infrastructure, fuel and electricity generation mix.
- **The sheet tabs in green**, generates all the figures and tables of the transport mode related emissions that are included in the ITF report. 
    - For example, the environmental impact of each transport mode in relation to per passenger-kilometer can be found in the sheet "Figure_2_GHG_per_pkm_General".

The tool itself contains predefined values based on the reflection of the current situation's global energy and transport system. If user wishes to modify the set values, the user can insert the input values into the colored cells of the sheets. For example, changes have been made to the sheet ''Power_Gen_Mix'' for the Excel file in this repository to reflect the electricity generation mix of Finland in 2020.

**More detailed information** about the tool can be found in the first sheet ''Introduction'' of the Excel file.

## Source

Cazzola, P. and Crist, P., 2020. Good to go? Assessing the environmental performance of new mobility. Available at: https://www.itf-oecd.org/good-go-assessing-environmental-performance-new-mobility (Accessed: 04 January 2023)

The electricity generation mix of Finland in 2020. Available at: https://www.iea.org/countries/finland (Accessed: 04 January 2023)

# About the CSV-file

The CSV file consists of GHG emissions per passenger-kilometer (g CO<sub>2</sub>/pkm) by transport modes derived from the mentioned LCA tool by ITF. The columns represent the different transport modes and the rows represent the GHG emissions. The GHG emissions of the transport modes have been divided into four separate components: vehicle component, fuel component, infrastructure component and operational services. The explanations of the acronyms (in the transport modes names) are: BEV = battery electric vehicle; HEV = hybrid electric vehicle; ICE = internal combustion engine; FCEV = fuel cell electric vehicle; PHEV = plug-in hybrid electric vehicle. 