import requests
import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse, unquote
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import io
import threading
import mimetypes

class UbuntuImageFetcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Ubuntu Image Fetcher")
        self.root.geometry("900x700")
        self.root.configure(bg='#f5f5f5')
        
        # Ubuntu-inspired color scheme
        self.ubuntu_orange = "#e95420"
        self.ubuntu_light = "#f5f5f5"
        self.ubuntu_dark = "#333333"
        
        # Set style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.ubuntu_light)
        self.style.configure('TLabel', background=self.ubuntu_light, foreground=self.ubuntu_dark)
        self.style.configure('TButton', background=self.ubuntu_orange, foreground='white')
        self.style.map('TButton', background=[('active', '#c34113')])
        self.style.configure('Header.TLabel', font=('Ubuntu', 18, 'bold'))
        self.style.configure('Title.TLabel', font=('Ubuntu', 12, 'bold'))
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = ttk.Label(self.header_frame, text="Ubuntu Image Fetcher", style='Header.TLabel')
        self.title_label.pack(side=tk.LEFT)
        
        self.ubuntu_quote = ttk.Label(self.header_frame, text="I am because we are", font=('Ubuntu', 10, 'italic'))
        self.ubuntu_quote.pack(side=tk.RIGHT)
        
        # Create URL input section
        self.url_frame = ttk.LabelFrame(self.main_frame, text="Image URLs (one per line)", padding=10)
        self.url_frame.pack(fill=tk.X, pady=10)
        
        self.url_text = scrolledtext.ScrolledText(self.url_frame, height=4, font=('Ubuntu', 10))
        self.url_text.pack(fill=tk.BOTH, expand=True)
        
        # Create options frame
        self.options_frame = ttk.Frame(self.main_frame)
        self.options_frame.pack(fill=tk.X, pady=10)
        
        self.duplicate_var = tk.BooleanVar(value=True)
        self.duplicate_check = ttk.Checkbutton(self.options_frame, text="Skip duplicate images", 
                                              variable=self.duplicate_var)
        self.duplicate_check.pack(side=tk.LEFT, padx=(0, 20))
        
        self.verify_var = tk.BooleanVar(value=True)
        self.verify_check = ttk.Checkbutton(self.options_frame, text="Verify image integrity", 
                                           variable=self.verify_var)
        self.verify_check.pack(side=tk.LEFT)
        
        # Create button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.fetch_btn = ttk.Button(self.button_frame, text="Fetch Images", command=self.start_fetch_thread)
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(self.button_frame, text="Clear URLs", command=self.clear_urls)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Create preview section
        self.preview_frame = ttk.LabelFrame(self.main_frame, text="Image Preview", padding=10)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_label = ttk.Label(self.preview_frame, text="Images will appear here after fetching", 
                                      background='white', anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Create status section
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready to fetch images from the community")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='determinate')
        self.progress.pack(side=tk.RIGHT, fill=tk.X, padx=(10, 0), expand=True)
        
        # Create directory info
        self.dir_frame = ttk.Frame(self.main_frame)
        self.dir_frame.pack(fill=tk.X, pady=5)
        
        self.dir_label = ttk.Label(self.dir_frame, text="Images are saved to: " + self.get_save_directory())
        self.dir_label.pack(side=tk.LEFT)
        
        self.open_dir_btn = ttk.Button(self.dir_frame, text="Open Folder", command=self.open_directory)
        self.open_dir_btn.pack(side=tk.RIGHT)
        
        # Create log area
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Activity Log", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=6, font=('Ubuntu', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state='disabled')
        
        # Ensure the directory exists
        self.create_directory()
        
        # Store downloaded image hashes to prevent duplicates
        self.downloaded_hashes = set()
        
        # Load existing image hashes
        self.load_existing_hashes()
        
    def get_save_directory(self):
        """Get the path to the Fetched_Images directory"""
        return os.path.join(os.path.expanduser("~"), "Fetched_Images")
        
    def create_directory(self):
        """Create the Fetched_Images directory if it doesn't exist"""
        directory = self.get_save_directory()
        os.makedirs(directory, exist_ok=True)
        return directory
        
    def open_directory(self):
        """Open the Fetched_Images directory in the file explorer"""
        directory = self.get_save_directory()
        if os.name == 'nt':
            os.startfile(directory)
        elif os.name == 'posix':
            os.system(f'open "{directory}"')
        else:
            os.system(f'xdg-open "{directory}"')
            
    def load_existing_hashes(self):
        """Load hashes of existing images to prevent duplicates"""
        directory = self.get_save_directory()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    self.downloaded_hashes.add(file_hash)
                except:
                    continue
                    
    def log_message(self, message):
        """Add a message to the log"""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        
    def clear_urls(self):
        """Clear the URL text area"""
        self.url_text.delete(1.0, tk.END)
        
    def start_fetch_thread(self):
        """Start the image fetching in a separate thread to avoid UI freezing"""
        urls = self.url_text.get(1.0, tk.END).strip().split('\n')
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showwarning("No URLs", "Please enter at least one image URL")
            return
            
        # Disable buttons during download
        self.fetch_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        
        # Reset progress bar
        self.progress['value'] = 0
        self.progress['maximum'] = len(urls)
        
        # Start download thread
        thread = threading.Thread(target=self.fetch_images, args=(urls,))
        thread.daemon = True
        thread.start()
        
    def fetch_images(self, urls):
        """Fetch multiple images from the provided URLs"""
        successful_downloads = 0
        
        for i, url in enumerate(urls):
            # Update status
            self.root.after(0, lambda: self.status_label.config(
                text=f"Fetching image {i+1} of {len(urls)}: {url[:50]}..." if len(url) > 50 else f"Fetching image {i+1} of {len(urls)}: {url}"))
            self.root.after(0, lambda: self.progress.step(1))
            
            try:
                # Validate URL
                if not url.startswith(('http://', 'https://')):
                    self.root.after(0, lambda: self.log_message(f"✗ Invalid URL: {url}"))
                    continue
                    
                # Send request with headers to mimic a browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'
                }
                
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                # Check content type to ensure it's an image
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type:
                    self.root.after(0, lambda: self.log_message(f"✗ URL does not point to an image: {url}"))
                    continue
                
                # Read image content
                image_content = response.content
                
                # Check for duplicates if enabled
                if self.duplicate_var.get():
                    file_hash = hashlib.md5(image_content).hexdigest()
                    if file_hash in self.downloaded_hashes:
                        self.root.after(0, lambda: self.log_message(f"⏭ Skipped duplicate image: {url}"))
                        continue
                    self.downloaded_hashes.add(file_hash)
                
                # Verify image integrity if enabled
                if self.verify_var.get():
                    try:
                        Image.open(io.BytesIO(image_content)).verify()
                    except:
                        self.root.after(0, lambda: self.log_message(f"✗ Invalid image file: {url}"))
                        continue
                
                # Extract filename from URL or generate one
                filename = self.extract_filename(url, content_type)
                save_path = os.path.join(self.get_save_directory(), filename)
                
                # Save the image
                with open(save_path, 'wb') as f:
                    f.write(image_content)
                    
                successful_downloads += 1
                self.root.after(0, lambda: self.log_message(f"✓ Successfully fetched: {filename}"))
                
                # Update preview with the last successfully downloaded image
                if successful_downloads == 1 or i == len(urls) - 1:
                    self.root.after(0, lambda: self.update_preview(image_content))
                    
            except requests.exceptions.RequestException as e:
                self.root.after(0, lambda: self.log_message(f"✗ Network error for {url}: {str(e)}"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"✗ Error processing {url}: {str(e)}"))
                
        # Update UI after all downloads
        self.root.after(0, self.download_finished(successful_downloads, len(urls)))
        
    def download_finished(self, successful, total):
        """Update UI after download process is complete"""
        self.fetch_btn.config(state=tk.NORMAL)
        self.clear_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Download completed: {successful} of {total} images fetched")
        
        if successful > 0:
            message = f"✓ Connection strengthened. Community enriched with {successful} new image(s)."
        else:
            message = "No new images were fetched. The community remains as is."
            
        self.log_message(message)
        
    def extract_filename(self, url, content_type):
        """Extract filename from URL or generate one based on content type"""
        # Try to get filename from URL
        parsed = urlparse(url)
        filename = os.path.basename(unquote(parsed.path))
        
        if not filename or '.' not in filename:
            # Generate filename based on content type
            ext = mimetypes.guess_extension(content_type) or '.jpg'
            if ext == '.jpe' or ext == '.jpeg':
                ext = '.jpg'
            filename = f"downloaded_image_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
            
        # Ensure filename is safe
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).rstrip()
        return safe_filename
        
    def update_preview(self, image_content):
        """Update the preview with the downloaded image"""
        try:
            image = Image.open(io.BytesIO(image_content))
            # Resize for preview while maintaining aspect ratio
            width, height = image.size
            max_size = 400
            if width > max_size or height > max_size:
                ratio = min(max_size/width, max_size/height)
                new_size = (int(width * ratio), int(height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Keep a reference
        except:
            self.preview_label.configure(text="Could not display preview")
            
def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = UbuntuImageFetcher(root)
    root.mainloop()

if __name__ == "__main__":
    main()