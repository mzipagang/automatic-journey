# Kroger Ad Platform API

[API Integration Document](./docs/Media%20Platform%20PLA%20API%20Integration.md)

Built on [Fast API Template](https://github.com/8451LLC/fastapi-internal-template)

## Local Development

Install [Poetry](https://python-poetry.org/docs/) if you do not already have it.

Ensure it is added to your PATH by running

```
poetry --version
```


Install local dependencies

```
poetry install
```

Run the application locally via docker with the command.

```
docker compose up -d
```

It can then be accessed at [localhost:8080](http://localhost:8080/)

## Local Linting

Run Linting using the command

```
poetry run pylint --recursive=y app
```

## Local Testing

Run Unit Testing using the command

```
./docker_run_tests.sh tests/unit
```

Run Integration Testing using the command

```
./docker_run_tests.sh tests/integration
```

Run All Testing using the command

```
./docker_run_tests.sh
```

To add code coverage to any of these commands simply add this flag after the pytest command

```
--cov=app
```

Which will look like

```
./docker_run_tests.sh --cov=app tests/unit
```

If you want to run tests locally without using Docker, you can first set the following variables in your terminal environment:
```bash
export REDIS_DB=0
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PRIMARY_ACCESS_KEY=
export REDIS_SSL=false
export REDIS_SOCKET_TIMEOUT=10
export REDIS_SOCKET_CONNECT_TIMEOUT=10
export ENV=local
```

Then you can run the following command to run all the unit tests:
```bash
poetry run pytest --cov=app tests/unit
```

## Docker

- Docker build command to build an image to use in AKS. (Needed for manual Helm Deploy)

```sh
# Build a docker image that can be used in AKS make sure to update the version
docker build -t docker-all.artifactory.8451.cloud/prism/build/map-onsite-apis:<version> --build-arg ARTIFACTORY_URL=artifactory.8451.cloud/artifactory/api/pypi/pypi-all/simple --platform linux/amd64 .
# Push the image to artifactory
docker push docker-all.artifactory.8451.cloud/prism/build/map-onsite-apis:<version>
```

## Helm Deployments

Helm Deployments will normally happen automatically in the pipeline. These below steps are for manual deployment.

## Kubernetes Login

Run this command to login to our kubernetes cluster before helm deploy

```sh
./scripts/loginToK8sCluster.sh sub-8451-aks-nonprod rg-aks-dev aks-ur-dev media-onsite-apis

./scripts/loginToK8sCluster.sh sub-8451-aks-nonprod rg-aks-stg aks-ur-stg media-onsite-apis
```

### Local Helm deploy steps

```sh
helm repo add stable https://artifactory.8451.cloud/artifactory/helm-all \
  --force-update \
  --pass-credentials \
  --username=$USER@8451.com
helm dependency build ./helm
helm upgrade media-onsite-apis helm/ --install --wait --namespace=media-onsite-apis --set=mediaOnsiteApis.image.tag=<tag> --set=mediaOnsiteApis.name=media-onsite-apis --version=<version> --values=helm/values.yaml --values=helm/values.<environment>.yaml
```

## A Note about Versioning

Versioning is intuitive with SDS's Github Actions Workflows. Unless configured otherwise, here are the details:

1. Typical branch commits will not affect your project's version i.e. tag.
2. Pull requests to main will, by default, bump the "patch" version. Example: `4.0.0` -> `4.0.1`
3. To establish a "minor" or "major" release, append either `#minor` or `#major` to the merge commit message!
   - Where is my merge commit message? It is the upper text box after clicking "Merge pull request" on a PR. [Example message](https://github.com/8451LLC/fastapi-internal-template/commit/d3df2339278ef5886ce0d1bdd70b9444cd9efa78)

**Additional Notes**

- By default, the template only runs Actions on a git push or manual run. Read how to add trigger events [here](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)
- If your project's file structure differs from the default template, you can still use this repo's Actions Workflows!
  - There are some values noted in **python-build-and-publish** that will need to be changed to suit your project structure.
  - If your helm chart directory is not _helm-chart/_, replace the values of **helm-chart-path** and **values-file-path** in **helm-package-and-publish** to the name of your helm directory
- In this version of the template, to deploy to dev, tst, stg, and prd, copy the helm-deploy-to-plg step in [helm_deploy.yaml](../.github/workflows/helm_deploy.yaml), changing values to the respective stage.
  - You should also copy [values.plg.yaml](../helm/fastapi-internal-template/values.plg.yaml), replacing the plg/dev values with the correct ones for your desired environment.

**Additional documentation:**

- [Setup Guide](https://confluence.kroger.com/confluence/display/8451EC/Step+by+Step+AKS+GitOps+Deployment+Guide)
- [GHA Official Documentation](https://docs.github.com/en/actions)
- [Helm Documentation](https://helm.sh/docs/)

## So, what's next?

1. Maturing your API:

- This template is setup to deploy a single example AKS fastapi to a playground environment. Clearly, this is for experimentation. As the following [84.51 SDLC Environment Documentation](https://azure-help-ui.prd.cdc2.cfapps.8451.com/content/best-practices/sdlc-enviroments.htm) details, your long-term goal for productionizing a product is always deployment to development, testing, staging, and production.

- Once your API is ready for multiple environments and needs to serve both developers in dev and consumers in prod, expand your Github Actions workflow by duplicating the Helm deployment stage. You will want one stage per environment. Perform simple name substitution where necessary on the duplicated stage (tst vs dev K8s namespaces, variable groups, etc.) for each new environment.

- You should also duplicate the [environment specific values yaml](helm/fastapi-internal-template/values.plg.yaml) for each deployment stage, substituting in appropriate values.

2. Are you sharing this API with a variety of consumers from different teams? Perhaps you want Role-Based-Access-Control! What does that mean? It means different endpoints can be only be accessed by users assigned to certain groups. Follow [these docs to enable this behavior](docs/RBAC_Auth_Example.md).

3. Lastly, you most likely want to limit who has access to the Production API, so follow the steps on [API Restrictions](https://confluence.kroger.com/confluence/display/8451EC/API+Restrictions).

## Observability

### Local

| Service                                                               |
| --------------------------------------------------------------------- |
| [jaeger](http://localhost:16686/search?service=media-onsite-apis) |

<!-- TODO: add other environments/service -->

### Plg

| Service                                                                                            |
| -------------------------------------------------------------------------------------------------- |
| [jaeger](https://jaeger-query.aks-ur-plg-internal.8451.cloud/search?service=media-onsite-apis) |

### Dev

| Service                                                                                            |
| -------------------------------------------------------------------------------------------------- |
| [jaeger](https://jaeger-query.aks-ur-dev-internal.8451.cloud/search?service=media-onsite-apis) |

### Tst

| Service                                                                                            |
| -------------------------------------------------------------------------------------------------- |
| [jaeger](https://jaeger-query.aks-ur-tst-internal.8451.cloud/search?service=media-onsite-apis) |

### Stg

| Service                                                                                            |
| -------------------------------------------------------------------------------------------------- |
| [jaeger](https://jaeger-query.aks-ur-stg-internal.8451.cloud/search?service=media-onsite-apis) |

### Prd

| Service                                                                                            |
| -------------------------------------------------------------------------------------------------- |
| [jaeger](https://jaeger-query.aks-ur-prd-internal.8451.cloud/search?service=media-onsite-apis) |

<!-- TODO: add other environments/service -->

### Manual Helm Deploy Using GitHub Actions

| Parameter                                 | Value             |
|:-----------------------------------------:|:-----------------:|
| Name for the helm release                 | map-onsite-apis   |
| Name of the helm chart is Chart.yaml      | media-onsite-apis |
| Version of the helm chart to be used      | x.x.x             |
| Namespace name in AKS                     | media-onsite-apis |
| Path to helm chart directory              | helm              |


### How to test your Feature Flags in Local?
If you request to add a new Feature Flag for you development you can
verify that is working in local by following these steps (Pycharm)
1. In your local configuration for Run/Debug include the next env variables:
    - ENV=local
    - HARNESS_API_KEY=****
    - HARNESS_OVERRIDES=project_truth_engine:True
    - REDIS_DB=0
    - REDIS_HOST=localhost
    - REDIS_PORT=6379
    - REDIS_PRIMARY_ACCESS_KEY=
    - REDIS_SSL=false
    - ROOT_CERT_PEM_PATH=/path/of/your/cert.pem
2. Go to app/decorators/cid_rate_limited.py
3. Print the config variable