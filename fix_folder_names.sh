#!/bin/bash

# Rename folders
mv src/1_presentation src/presentation
mv src/2_application src/application
mv src/3_domain src/domain
mv src/4_infrastructure src/infrastructure

# Fix all imports in Python files
find . -name "*.py" -type f -exec sed -i '' 's/src\.1_presentation/src.presentation/g' {} +
find . -name "*.py" -type f -exec sed -i '' 's/src\.2_application/src.application/g' {} +
find . -name "*.py" -type f -exec sed -i '' 's/src\.3_domain/src.domain/g' {} +
find . -name "*.py" -type f -exec sed -i '' 's/src\.4_infrastructure/src.infrastructure/g' {} +

echo "✅ Folder names fixed!"
echo "✅ All imports updated!"
