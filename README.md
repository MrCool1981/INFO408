# Project: INFO408 Project

## Description

The goal of this project is to design and construct a database that can accommodate a large-scale data set using a suitable database management system (DBMS). This involves selecting a data set and a target DBMS, creating a database design, implementing the design in the chosen DBMS, and documenting the design and implementation process.

The chosen dataset should be freely available online, contain between 100 MB and 2 GB of data, and display some internal complexity. It should also require some transformation before being loaded into the chosen database.

The project's focus is on the design and construction of the database, rather than the analysis of the dataset. Depending on the chosen dataset and DBMS, the design requirements may vary. The final step involves importing the dataset into the built database using appropriate import tools or a custom program.

The outcome of the project is a short technical report documenting the database design and implementation process. This report will include an overview of the dataset, a justification for the DBMS choice, a detailed discussion of the database implementation, and a discussion of the dataset importation process.

## Solution

**Dataset:** The dataset used in this project is the Serum metabolites data, which is freely available in XML format from the [Human Metabolome Database (HMDB)](https://hmdb.ca/).

**Target Database:** The target database for this project is [Microsoft Azure Cosmos DB](https://azure.microsoft.com/en-us/products/cosmos-db), utilizing its NoSQL API.

**Interactive Tool:** A simple webapp with a sample search example.

**Tools Used:** The tools utilized in this project include the Python SDK for Azure Cosmos DB NoSQL API, Jupyter Notebook for data manipulation, and Flask for the back-end of the web application. For the front-end of the web application, HTML, Jinja templates, CSS, and Bootstrap were used. The project was deployed using Azure Cosmos DB, Azure WebApp, and Azure AppService, along with various Python packages to assist in the development process.