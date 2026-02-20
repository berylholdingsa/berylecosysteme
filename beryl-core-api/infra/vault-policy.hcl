# Policy used by beryl-core-api runtime and rotation automation.
# Keep this policy restricted to the minimum required paths.

path "secret/data/beryl-core-api/prod/*" {
  capabilities = ["read"]
}

path "secret/data/beryl-core-api/staging/*" {
  capabilities = ["read"]
}

path "secret/data/beryl-core-api/keys/*" {
  capabilities = ["read", "create", "update", "list"]
}

path "transit/keys/beryl-core-api" {
  capabilities = ["read", "create", "update"]
}

path "transit/sign/beryl-core-api" {
  capabilities = ["update"]
}

path "transit/verify/beryl-core-api" {
  capabilities = ["update"]
}
