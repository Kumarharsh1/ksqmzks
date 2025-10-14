import pdfplumber
import aiofiles
import os
from fastapi import UploadFile, HTTPException

class FileProcessor:
    async def process_file(self, file: UploadFile) -> str:
        try:
            contents = await file.read()
            
            # Validate file size (10MB)
            if len(contents) > 10 * 1024 * 1024:
                raise HTTPException(400, "File size exceeds 10MB limit")
            
            # Process based on file type
            if file.filename.lower().endswith('.pdf'):
                return await self._process_pdf(contents)
            elif file.filename.lower().endswith('.txt'):
                return await self._process_txt(contents)
            else:
                raise HTTPException(400, "Unsupported file format")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"File processing failed: {str(e)}")

    async def _process_pdf(self, contents: bytes) -> str:
        try:
            # Write to temporary file
            temp_path = "temp.pdf"
            with open(temp_path, "wb") as f:
                f.write(contents)
            
            # Extract text from PDF
            text_content = ""
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content += text + "\n"
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return text_content.strip()
            
        except Exception as e:
            raise Exception(f"PDF processing error: {str(e)}")

    async def _process_txt(self, contents: bytes) -> str:
        try:
            return contents.decode('utf-8')
        except UnicodeDecodeError:
            raise Exception("File encoding not supported")