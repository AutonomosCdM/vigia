#!/usr/bin/env python3
"""
Script para descargar recursos adicionales de ulceras.cl
"""

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from pathlib import Path
import time

def scrape_ulceras_cl():
    """Scrape ulceras.cl para encontrar documentos relevantes de LPP"""
    
    base_url = "https://ulceras.cl"
    target_url = "https://ulceras.cl/recursos/guias-y-documentos/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        print(f"Accediendo a {target_url}...")
        response = requests.get(target_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar enlaces a documentos PDF
        links = soup.find_all('a', href=True)
        pdf_links = []
        
        keywords = ['lpp', 'upp', 'ulcera', 'presion', 'lesion', 'pressure', 'wound']
        
        for link in links:
            href = link['href']
            link_text = link.get_text().lower()
            
            # Verificar si es un PDF y contiene palabras clave relevantes
            if (href.endswith('.pdf') or '.pdf' in href) and any(keyword in (href.lower() + ' ' + link_text) for keyword in keywords):
                
                # Convertir URLs relativas a absolutas
                if href.startswith('/'):
                    full_url = base_url + href
                elif not href.startswith('http'):
                    full_url = urllib.parse.urljoin(target_url, href)
                else:
                    full_url = href
                    
                pdf_links.append({
                    'url': full_url,
                    'text': link.get_text().strip(),
                    'filename': os.path.basename(urllib.parse.urlparse(href).path)
                })
        
        print(f"Encontrados {len(pdf_links)} documentos potenciales:")
        for i, link_info in enumerate(pdf_links, 1):
            print(f"{i}. {link_info['text']} -> {link_info['filename']}")
        
        # Crear directorio de destino
        output_dir = Path("vigia_detect/references/minsal/ulceras_cl")
        output_dir.mkdir(exist_ok=True)
        
        downloaded_files = []
        
        # Descargar documentos (máximo 5 para evitar sobrecarga)
        for i, link_info in enumerate(pdf_links[:5]):
            try:
                print(f"\nDescargando {link_info['url']}...")
                
                doc_response = requests.get(link_info['url'], headers=headers, timeout=60)
                doc_response.raise_for_status()
                
                # Generar nombre de archivo seguro
                safe_filename = f"ulceras_cl_doc_{i+1}_{link_info['filename']}"
                if not safe_filename.endswith('.pdf'):
                    safe_filename += '.pdf'
                
                output_path = output_dir / safe_filename
                
                with open(output_path, 'wb') as f:
                    f.write(doc_response.content)
                
                downloaded_files.append({
                    'path': str(output_path),
                    'url': link_info['url'],
                    'title': link_info['text'],
                    'size': len(doc_response.content)
                })
                
                print(f"✓ Descargado: {safe_filename} ({len(doc_response.content)} bytes)")
                time.sleep(2)  # Pausa entre descargas
                
            except Exception as e:
                print(f"✗ Error descargando {link_info['url']}: {e}")
                continue
        
        print(f"\n✓ Descarga completada. {len(downloaded_files)} archivos descargados.")
        return downloaded_files
        
    except requests.RequestException as e:
        print(f"Error accediendo a {target_url}: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado: {e}")
        return []

if __name__ == "__main__":
    downloaded = scrape_ulceras_cl()
    
    if downloaded:
        print("\nArchivos descargados:")
        for file_info in downloaded:
            print(f"- {file_info['path']} ({file_info['size']} bytes)")
    else:
        print("No se descargaron archivos.")