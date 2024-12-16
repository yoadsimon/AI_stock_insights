# Airflow Docker Setup

This project sets up an Apache Airflow environment using Docker and Docker Compose. The configuration is customized to:

- Exclude the default example DAGs.
- Set the default timezone to `US/Eastern`.
- Provide a ready-to-use Airflow setup for deployment on a virtual machine (VM).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
    - [Clone the Repository](#clone-the-repository)
    - [Create Necessary Directories and Set Environment Variables](#create-necessary-directories-and-set-environment-variables)
    - [Modify `docker-compose.yaml` Configuration](#modify-docker-composeyaml-configuration)
    - [Initialize the Airflow Environment](#initialize-the-airflow-environment)
    - [Start Airflow Services](#start-airflow-services)
    - [Create an Admin User](#create-an-admin-user)
    - [Access the Airflow Web Interface](#access-the-airflow-web-interface)
- [Managing the Airflow Environment](#managing-the-airflow-environment)
    - [Starting Services](#starting-services)
    - [Stopping Services](#stopping-services)
    - [Viewing Logs](#viewing-logs)
- [Customizing the Setup](#customizing-the-setup)
    - [Adding Python Packages](#adding-python-packages)
    - [Using a Custom `airflow.cfg` File](#using-a-custom-airflowcfg-file)
- [Deploying on a Virtual Machine](#deploying-on-a-virtual-machine)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)
- [References](#references)

---

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Docker**: Verify the installation with:

  ```bash
  docker --version
  ```

- **Docker Compose**: Version **2.14.0** or newer. Verify with:

  ```bash
  docker compose version
  ```

---

## Installation Steps

### Clone the Repository

Clone this repository to your local machine:

```bash
git clone <repository-url>
cd <repository-directory>
```

Replace `<repository-url>` with the URL of your repository and `<repository-directory>` with the name of the cloned
directory.

---

### Create Necessary Directories and Set Environment Variables

Create the required directories and set up the environment variables for Airflow.

```bash
# Create directories
mkdir -p ./dags ./logs ./plugins ./config

# Set the AIRFLOW_UID environment variable
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Set additional Airflow configurations in the .env file
echo 'AIRFLOW__CORE__LOAD_EXAMPLES=False' >> .env
echo 'AIRFLOW__CORE__DEFAULT_TIMEZONE=US/Eastern' >> .env
```

---

### Modify `docker-compose.yaml` Configuration

Ensure your `docker-compose.yaml` file has the correct configurations.

1. **Open `docker-compose.yaml` in a text editor**:

   ```bash
   cat docker-compose.yaml | grep "AIRFLOW__CORE__LOAD_EXAMPLES"
   vi docker-compose.yaml
   ```

2. **Modify the `x-airflow-common` section**:

   Locate the `x-airflow-common` anchor in the file and set `AIRFLOW__CORE__LOAD_EXAMPLES` to `'false'`

   ```yaml
    /AIRFLOW__CORE__LOAD_EXAMPLES
   ```
    ```yaml
   AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
   ```


3. **Save and exit**:

    - esc -> `:wq` -> enter

---

### Initialize the Airflow Environment

Before starting Airflow, initialize the environment to set up the metadata database and create the necessary tables.

1. **Stop any running containers and remove volumes (if any)**:

   ```bash
   docker compose down --volumes --remove-orphans
   ```

2. **Initialize Airflow**:

   ```bash
   docker compose up airflow-init
   ```

    - This command sets up the Airflow metadata database without loading the example DAGs.

3. **Wait for the initialization to complete**:

    - The process is complete when you see a message like:

      ```
      airflow-init_1  | 2.7.1
      airflow-init_1 exited with code 0
      ```

---

### Start Airflow Services

Start all Airflow services in detached mode:

```bash
docker compose up -d
```

---

### Create an Admin User

Create an admin user to access the Airflow web interface.

```bash
docker compose run airflow-worker airflow users create \
    --username YOUR_USERNAME \
    --firstname YOUR_FIRST_NAME \
    --lastname YOUR_LAST_NAME \
    --role Admin \
    --email YOUR_EMAIL \
    --password YOUR_PASSWORD
```

- Replace `YOUR_USERNAME`, `YOUR_FIRST_NAME`, `YOUR_LAST_NAME`, `YOUR_EMAIL`, and `YOUR_PASSWORD` with your desired
  credentials.

---

### Access the Airflow Web Interface

Start Airflow:

```bash
docker compose up
```

1. **Open your web browser** and navigate to:

   ```
   http://localhost:8080
   ```

2. **Log in** using the credentials you created.

3. **Verify the setup**:

    - **Time Zone**: Click on your username in the top-right corner, select **About**, and ensure the **Timezone** is
      set to `US/Eastern`.
    - **Example DAGs**: The list of DAGs should only include your custom DAGs placed in the `./dags` directory. The
      default example DAGs should not appear.

---

## Managing the Airflow Environment

### Starting Services

To start the Airflow services:

```bash
docker compose up -d
```

### Stopping Services

To stop the Airflow services:

```bash
docker compose down
```

### Viewing Logs

To view logs for all services:

```bash
docker compose logs -f
```

To view logs for a specific service (e.g., `airflow-webserver`):

```bash
docker compose logs -f airflow-webserver
```

---

## Customizing the Setup

### Adding Python Packages

If your DAGs require additional Python packages, you can customize the Airflow image.

1. **Create a `requirements.txt` file**:

   ```bash
   touch requirements.txt
   ```

2. **Add your required packages** to `requirements.txt`:

   ```text
   package_one
   package_two
   ```

3. **Modify `docker-compose.yaml` to build a custom image**:

    - Comment out the `image:` line and uncomment the `build:` line in the `x-airflow-common` section:

      ```yaml
      x-airflow-common:
        &airflow-common
        # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.7.1}
        build: .
        # ... rest of configurations ...
      ```

4. **Create a `Dockerfile` in the project directory**:

   ```bash
   touch Dockerfile
   ```

   Add the following content to the `Dockerfile`:

   ```dockerfile
   FROM apache/airflow:2.7.1
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   ```

5. **Rebuild the Airflow image**:

   ```bash
   docker compose build
   ```

6. **Start the services**:

   ```bash
   docker compose up -d
   ```

### Using a Custom `airflow.cfg` File

If you prefer to use a custom `airflow.cfg` file:

1. **Create a custom configuration directory**:

   ```bash
   mkdir -p ./config
   ```

2. **Obtain the default `airflow.cfg`**:

   ```bash
   docker run --rm apache/airflow:2.7.1 cat /opt/airflow/airflow.cfg > config/airflow.cfg
   ```

3. **Modify the `config/airflow.cfg`** file as needed (e.g., set `load_examples = False`,
   `default_timezone = US/Eastern`).

4. **Mount the configuration in `docker-compose.yaml`**:

   Under each Airflow service, add:

   ```yaml
   volumes:
     - ./config/airflow.cfg:/opt/airflow/airflow.cfg
   ```

5. **Restart the Airflow services**:

   ```bash
   docker compose down
   docker compose up -d
   ```

---

## Deploying on a Virtual Machine

To deploy this setup on a VM:

1. **Transfer the project files** to the VM.

2. **Install Docker and Docker Compose** on the VM if they are not already installed.

3. **Follow the setup instructions** from the [Installation Steps](#installation-steps) section.

4. **Adjust host-specific configurations** if necessary (e.g., updating `localhost` references in `docker-compose.yaml`
   to point to the VM's IP address).

---

## Troubleshooting

- **Example DAGs Still Visible**:

    - Ensure `AIRFLOW__CORE__LOAD_EXAMPLES` is set to `'false'` in the `docker-compose.yaml` under the
      `x-airflow-common` environment variables.
    - Remove any existing volumes and reinitialize the environment:

      ```bash
      docker compose down --volumes --remove-orphans
      docker compose up airflow-init
      ```

- **Time Zone Not Updated**:

    - Verify `AIRFLOW__CORE__DEFAULT_TIMEZONE` is correctly set in `docker-compose.yaml`.
    - Restart the Airflow services:

      ```bash
      docker compose down
      docker compose up -d
      ```

- **Environment Variables Not Applying**:

    - Ensure there are no typos in the variable names.
    - Environment variables in `docker-compose.yaml` override those in `.env`. Make sure the variables are correctly set
      in the `docker-compose.yaml`.

- **Memory Issues on macOS or Windows**:

    - Allocate at least **4GB** of memory to Docker to prevent the webserver from continuously restarting.

---

## Credits

This setup is based on the
official [Apache Airflow Docker Compose example](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
and has been customized to meet project-specific requirements.

---

## References

- [Apache Airflow Official Documentation](https://airflow.apache.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
