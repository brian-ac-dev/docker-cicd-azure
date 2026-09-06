# Configuración de OIDC para GitHub Actions en Azure

Este documento detalla los pasos para configurar una relación de confianza (Federated Trust) entre GitHub Actions y Azure usando OpenID Connect (OIDC). Este método elimina la necesidad de gestionar secretos estáticos que expiran.

## Requisitos Previos

Antes de comenzar, es obligatorio iniciar sesión en Azure desde la terminal.

```bash
az login
```

Asegúrese de estar en la suscripción correcta (si tiene múltiples suscripciones):
```bash
az account set --subscription "NOMBRE_O_ID_DE_SUSCRIPCION"
```

## Configuración Paso a Paso

El siguiente bloque de código contiene todos los comandos necesarios. Solo debe modificar las variables iniciales antes de ejecutarlo.

### 1. Definir Variables

Reemplace `TU_USUARIO` y `TU_REPO` con la información correspondiente a su repositorio en GitHub.

```bash
GITHUB_USER="TU_USUARIO"
GITHUB_REPO="TU_REPO"
APP_NAME="github-actions-$GITHUB_REPO-app"
```

### 2. Ejecutar Script de Configuración

Copie y pegue el siguiente bloque completo en su terminal. El script realizará las siguientes acciones:
1. Obtendrá los IDs de su Tenant y Suscripción.
2. Creará una App Registration en Entra ID.
3. Creará el Service Principal asociado.
4. Asignará el rol de 'Contributor' a la aplicación.
5. Configurará la credencial federada (OIDC) para la rama `main` del repositorio indicado.

```bash
# Obtener IDs de la cuenta actual
SUB_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "-> Tenant ID: $TENANT_ID"
echo "-> Subscription ID: $SUB_ID"

# Crear App Registration
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
echo "-> Client ID (App ID): $APP_ID"

# Crear Service Principal
SP_ID=$(az ad sp create --id $APP_ID --query id -o tsv)

# Esperar unos segundos para la propagación del Service Principal en Entra ID
echo "Esperando a que se propague la identidad..."
sleep 15

# Asignar rol de Contributor a la suscripción
az role assignment create \
  --role contributor \
  --subscription $SUB_ID \
  --assignee-object-id $SP_ID \
  --assignee-principal-type ServicePrincipal \
  --scope /subscriptions/$SUB_ID

# Crear Credencial Federada OIDC
az ad app federated-credential create --id $APP_ID --parameters '{
  "name": "github-actions-trust",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:'$GITHUB_USER'/'$GITHUB_REPO':ref:refs/heads/main",
  "description": "Acceso OIDC desde GitHub Actions",
  "audiences": ["api://AzureADTokenExchange"]
}'

echo "========================================="
echo "CONFIGURACIÓN COMPLETADA"
echo "Copie los siguientes valores en GitHub Secrets:"
echo "AZURE_TENANT_ID: $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUB_ID"
echo "AZURE_CLIENT_ID: $APP_ID"
echo "========================================="
```

## Configuración en GitHub

Una vez que el script termine, complete la integración del lado de GitHub:

1. Vaya a su repositorio en GitHub.
2. Navegue a **Settings > Secrets and variables > Actions**.
3. Haga clic en **New repository secret**.
4. Agregue los 3 secretos (`AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` y `AZURE_CLIENT_ID`) con los valores que imprimió la terminal.

5. Configure el workflow con `azure/login@v2` usando OIDC (no requiere client secret):

```yaml
permissions:
  id-token: write
  contents: read

- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

> **Nota:** OIDC requiere permisos de directorio en Entra ID para crear App Registrations. Si recibe el error *"Directory permission is needed for the current user to register the application"*, use la alternativa descrita a continuación.

---

## Alternativa: ACR + Publish Profile (sin App Registration)

Use este método cuando **no tenga permisos en Entra ID** para crear App Registrations (común en entornos de laboratorio como Real Hands-On Labs). Solo necesita permisos sobre el Resource Group donde están el Azure Container Registry (ACR) y el App Service.

### Cuándo usar cada método

| Método | ¿Puede hacerlo usted? | Secretos en GitHub |
|--------|------------------------|--------------------|
| OIDC | Requiere rol de directorio (Application Administrator, etc.) | 3 secretos (sin password) |
| **ACR + Publish Profile** | **Sí, con permisos sobre el RG** | 3 secretos (credenciales estáticas) |
| Service Principal + client secret | Requiere rol de directorio para crear la app | 1 secreto JSON |

### 1. Definir Variables

```bash
RESOURCE_GROUP="NOMBRE_DE_SU_RESOURCE_GROUP"
ACR_NAME="NOMBRE_DE_SU_ACR"
WEBAPP_NAME="NOMBRE_DE_SU_APP_SERVICE"
IMAGE_NAME="NOMBRE_IMAGEN"   # ej: docker-cicd-azure
```

### 2. Obtener Credenciales del ACR

Habilite el usuario administrador del registro y obtenga usuario/contraseña:

```bash
az acr update -n $ACR_NAME --admin-enabled true -g $RESOURCE_GROUP

az acr credential show -n $ACR_NAME -g $RESOURCE_GROUP \
  --query "{username:username, password:passwords[0].value}" -o json
```

Anote el `loginServer` del ACR:

```bash
az acr show -n $ACR_NAME -g $RESOURCE_GROUP --query loginServer -o tsv
```

### 3. Obtener Publish Profile del App Service (Hacerlo manual en el portal)

Copie el XML completo

### 4. Configuración en GitHub

Agregue estos secretos en **Settings > Secrets and variables > Actions**:

| Secret | Valor |
|--------|-------|
| `ACR_USERNAME` | Username del ACR (salida de `az acr credential show`) |
| `ACR_PASSWORD` | Password del ACR (salida de `az acr credential show`) |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | XML completo del publish profile |

### 5. Workflow de Ejemplo

Reemplace `NOMBRE_ACR.azurecr.io` y `NOMBRE_IMAGEN` según su entorno:

```yaml
name: Azure CI CD DOCKER

on:
  push:
    branches: [main]

env:
  IMAGE_NAME: NOMBRE_ACR.azurecr.io/NOMBRE_IMAGEN

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: NOMBRE_ACR.azurecr.io
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Deploy to App Service
        uses: azure/webapps-deploy@v3
        with:
          app-name: NOMBRE_APP_SERVICE
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          images: ${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### Consideraciones

- **Ventaja:** funciona sin permisos de Entra ID; solo necesita acceso al Resource Group.
- **Inconveniente:** usa secretos estáticos. Si regenera las credenciales del ACR o el publish profile, debe actualizar los secretos en GitHub.
- El App Service debe estar configurado para ejecutar contenedores Linux (`linuxFxVersion` con prefijo `DOCKER|`).
