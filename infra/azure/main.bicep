targetScope = 'resourceGroup'

param prefix string
param location string
param sqlLocation string
param storageName string
param repository string
param repositoryId int
param ownerId int
param readerObjectIds array
param setupObjectId string
@secure()
param sqlAdminPassword string

var tags = { project: 'picky-assignment-2', student: prefix }
var services = ['restaurants', 'dining']

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false // Static website remains public; ordinary blobs do not.
    allowSharedKeyAccess: false
  }
}
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}
resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
  }
}
resource sql 'Microsoft.Sql/servers@2023-08-01' = {
  name: '${prefix}-sql'
  location: sqlLocation
  tags: tags
  properties: {
    administratorLogin: 'pickyadmin'
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    version: '12.0'
  }
}
resource databases 'Microsoft.Sql/servers/databases@2023-08-01' = [for service in services: {
  parent: sql
  name: '${prefix}-${service}-db'
  location: sqlLocation
  tags: tags
  sku: { name: 'GP_S_Gen5', tier: 'GeneralPurpose', family: 'Gen5', capacity: 1 }
  properties: {
    minCapacity: json('0.5')
    useFreeLimit: true
    freeLimitExhaustionBehavior: 'AutoPause'
    requestedBackupStorageRedundancy: 'Local'
    // Free offer fixes size/auto-pause defaults; deliberately do not override them.
  }
}]
resource azureFirewall 'Microsoft.Sql/servers/firewallRules@2023-08-01' = {
  parent: sql
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-github'
  location: location
  tags: tags
}
var subjects = [
  'repo:${repository}:ref:refs/heads/main'
  'repo:${split(repository, '/')[0]}@${ownerId}/${split(repository, '/')[1]}@${repositoryId}:ref:refs/heads/main'
]
resource federation 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = [for (subject, i) in subjects: {
  parent: identity
  name: 'github-main-${i}'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    audiences: ['api://AzureADTokenExchange']
    subject: subject
  }
}]
resource contributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, identity.id, 'contributor')
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
  }
}
resource blobWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, identity.id, 'blob-writer')
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}
// The signed-in bootstrap operator needs this data-plane role to enable the site.
resource setupBlobWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, setupObjectId, 'setup-blob-writer')
  properties: {
    principalId: setupObjectId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}
resource readers 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for objectId in readerObjectIds: {
  name: guid(resourceGroup().id, objectId, 'reader')
  properties: {
    principalId: objectId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'acdd72a7-3385-48ef-bd42-f606fba81ae7')
  }
}]
output clientId string = identity.properties.clientId
output environmentId string = environment.id
output sqlHost string = sql.properties.fullyQualifiedDomainName
output storageAccount string = storage.name
