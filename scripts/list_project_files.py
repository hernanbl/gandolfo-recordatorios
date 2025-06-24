import os
import sys
import importlib
import pkgutil
import inspect

def get_project_files(start_dir):
    """
    Recorre el directorio del proyecto y lista todos los archivos Python.
    """
    project_files = []
    
    for root, dirs, files in os.walk(start_dir):
        # Ignorar directorios ocultos y directorios de entorno virtual
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != 'env']
        
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start_dir)
                project_files.append((relative_path, full_path))
    
    return project_files

def analyze_imports(project_files):
    """
    Analiza los archivos para determinar las importaciones y dependencias.
    """
    dependencies = {}
    
    for rel_path, full_path in project_files:
        with open(full_path, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                imports = []
                
                # Buscar líneas de importación
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
                
                dependencies[rel_path] = imports
            except Exception as e:
                print(f"Error al analizar {full_path}: {str(e)}")
    
    return dependencies

def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Analizando proyecto en: {project_dir}")
    
    # Obtener todos los archivos Python del proyecto
    project_files = get_project_files(project_dir)
    print(f"Se encontraron {len(project_files)} archivos Python en el proyecto.")
    
    # Analizar importaciones
    dependencies = analyze_imports(project_files)
    
    # Mostrar archivos y sus importaciones
    print("\nArchivos del proyecto y sus importaciones:")
    print("="*80)
    
    for file_path, imports in dependencies.items():
        print(f"\n{file_path}:")
        for imp in imports:
            print(f"  - {imp}")
    
    # Listar archivos principales (scripts ejecutables)
    print("\nArchivos principales (posibles puntos de entrada):")
    print("="*80)
    
    for rel_path, full_path in project_files:
        if rel_path.startswith('scripts/') or 'main' in rel_path:
            print(f"- {rel_path}")

if __name__ == "__main__":
    main()