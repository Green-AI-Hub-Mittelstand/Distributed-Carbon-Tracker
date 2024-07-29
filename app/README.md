<a name="readme-top"></a>

<br />
<div align="center">
  <h1 align="center">Carbon Tracker</h1>
  
  <p align="center">
    <a href="https://github.com/Green-AI-Hub-Mittelstand/readme_template/issues">Report Bug</a>
    ·
    <a href="https://github.com/Green-AI-Hub-Mittelstand/readme_template/issues">Request Feature</a>
  </p>

  <br />

  <p align="center">
    <a href="https://www.green-ai-hub.de">
    <img src="images/green-ai-hub-keyvisual.svg" alt="Logo" width="80%">
  </a>
    <br />
    <h3 align="center"><strong>Green-AI Hub Mittelstand</strong></h3>
    <a href="https://www.green-ai-hub.de"><u>Homepage</u></a> 
    | 
    <a href="https://www.green-ai-hub.de/kontakt"><u>Contact</u></a>
  
   
  </p>
</div>

<br/>

## About The Project

This repository provides a comprehensive solution for tracking the environmental impact of machine learning (ML) applications. Designed to offer insights into the power usage and carbon dioxide emissions associated with training and inference processes, it encompasses a Client, a Server, a connected Database, and a dashboard for visualizing the results.

### Architecture

1. Client: The Client component serves as the interface through which users interact with the Carbon Tracker system. Users can submit their ML code for analysis, specifying parameters such as the training dataset, inference workload, and hardware configuration.

2. Server: The Server component acts as the central processing unit of the Carbon Tracker system. Upon receiving input from the Client, it orchestrates the execution of ML tasks, monitors resource consumption, and calculates associated carbon emissions. The Server is responsible for managing the interaction between various system modules and ensuring smooth operation.

3. Database: The connected Database serves as the repository for storing relevant data generated during the tracking process. This includes information such as power usage metrics, carbon emissions estimates, hardware specifications, and execution times. The Database facilitates data retrieval for subsequent analysis and visualization.

4. Dashboard: The resulting dashboard provides users with a graphical representation of the environmental impact of their ML applications. Through intuitive visualizations, users can gain insights into the energy consumption, CO2 emissions, and runtime performance of their algorithms. The dashboard enables users to make informed decisions regarding optimization strategies and resource allocation.

### Functionality

1. Tracking ML Workloads: The Carbon Tracker system tracks both the training and inference phases of ML applications. It captures resource utilization metrics such as CPU/GPU usage for a varying number of computing units.

2. Carbon Emission Estimation: By correlating resource usage data with corresponding carbon emission factors, the system calculates the environmental impact of ML tasks. This includes estimating the amount of CO2 emissions generated during the execution of algorithms, as well as comparing the execution times.

3. Customization and Scalability: The Carbon Tracker repository offers flexibility for customization according to user requirements and supports scalability to accommodate varying workload sizes and hardware configurations.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Table of Contents

<details>
  <summary><img src="images/table_of_contents.jpg" alt="Logo" width="2%"></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li><a href="#table-of-contents">Table of Contents</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

Clone this repository, navigate with your terminal into this repository and execute the following steps.

### Prerequisites

Basically all prerequisites are installed by executing below installation step.

Alternatively when cloning the whole repository use following command to install them.

```sh
pip install -r requirements.txt
```

### Installation

Installing using pip: pip install carbontracking

Alternatively clone the repository using git clone https://git.opendfki.de/gaih/carbon_tracker.git

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

Usage is displayed in following colab notebook:
https://colab.research.google.com/drive/1AsMpi_7Tdr8Rmd2oFDK5qvPyLJl5XH6W?usp=sharing

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Green-AI Hub Mittelstand - info@green-ai-hub.de

Project Link: https://github.com/Green-AI-Hub-Mittelstand/repository_name

<br />
  <a href="https://www.green-ai-hub.de/kontakt"><strong>Get in touch »</strong></a>
<br />
<br />

<p align="left">
    <a href="https://www.green-ai-hub.de">
    <img src="images/green-ai-hub-mittelstand.svg" alt="Logo" width="45%">
  </a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>
