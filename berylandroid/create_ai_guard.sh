#!/bin/bash

GUARD_FILE="AI_GUARD_PATCH_STRICT.txt"

cat << 'EOT' > "$GUARD_FILE"
CONTRAINTE ABSOLUE – À RESPECTER STRICTEMENT

- Interdiction formelle de supprimer, renommer ou réécrire du code existant.
- Interdiction de modifier la structure des fichiers existants.
- Toute modification doit être :
  - minimale
  - incrémentale
  - localisée
  - sous forme de PATCH uniquement.
- Si une correction est nécessaire :
  - indiquer précisément le fichier
  - indiquer précisément la ligne
  - fournir uniquement le diff ou le bloc à ajouter.
- Tout code existant est considéré comme VALIDÉ, STRATÉGIQUE et NON NÉGOCIABLE.
- Si une information manque, NE PAS SUPPOSER : demander clarification.
EOT

echo "✅ Fichier \$GUARD_FILE créé avec succès."
