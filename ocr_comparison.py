import os
import subprocess
import boto3
import json

# ---- CONFIG ----
IMAGE_DIR = "test_images"
RESULTS_DIR = "results"
USE_ANALYZE_DOCUMENT = False  # Textract: True for forms/tables
TESS_LANG = "eng"

# ---- TESSERACT ----
def run_tesseract(image_path, output_base):
	# Output plain text
	subprocess.run([
		"tesseract",
		image_path,
		output_base,
		"-l", "eng",
		"--psm", "3",
		"--oem", "1"
	], check=True)

	# Output hOCR
	subprocess.run([
		"tesseract",
		image_path,
		output_base,
		"-l", "eng",
		"--psm", "3",
		"--oem", "1",
		"hocr"
	], check=True)

# ---- TEXTRACT ----
def textract_client():
	session = boto3.Session(profile_name="textract-test")
	return session.client("textract", region_name="us-east-1")

def run_textract(image_path):
	client = textract_client()
	with open(image_path, 'rb') as f:
		image_bytes = f.read()

		if USE_ANALYZE_DOCUMENT:
			response = client.analyze_document(
				Document={'Bytes': image_bytes},
				FeatureTypes=["FORMS"]
			)
		else:
			response = client.detect_document_text(Document={'Bytes': image_bytes})
	return response

def extract_text_from_textract(response):
	lines = []
	for block in response.get("Blocks", []):
		if block["BlockType"] == "LINE":
			lines.append(block["Text"])
	return "\n".join(lines)

# ---- JP2 CONVERSION ----
def convert_jp2_to_jpeg(input_path):
	jpg_path = input_path.replace(".jp2", ".jpg")
	if not os.path.exists(jpg_path):
		print(f"📷 Converting {input_path} to {jpg_path} with contrast enhancement...")
		subprocess.run([
			"convert", input_path,
			"-resize", "100%",
			# "-colorspace", "Gray",
			# "-contrast",           # Apply contrast enhancement (can be repeated)
			# "-contrast",
			# "-strip",
			"-quality", "100",
			jpg_path
		], check=True)
	return jpg_path

# ---- MAIN ----
def process_image(image_path):
	base_filename = os.path.splitext(os.path.basename(image_path))[0]
	out_dir = os.path.join(RESULTS_DIR, base_filename)
	os.makedirs(out_dir, exist_ok=True)

	# Handle JP2 conversion
	if image_path.lower().endswith(".jp2"):
		image_path = convert_jp2_to_jpeg(image_path)

	# Tesseract OCR
	print(f"🟢 Tesseract: {base_filename}")
	tess_out_base = os.path.join(out_dir, "tesseract")
	run_tesseract(image_path, tess_out_base)

	# Textract OCR
	print(f"🔵 Textract: {base_filename}")
	try:
		textract_result = run_textract(image_path)
		with open(os.path.join(out_dir, "textract.json"), "w", encoding="utf-8") as f:
			json.dump(textract_result, f, indent=2)
		text = extract_text_from_textract(textract_result)
		with open(os.path.join(out_dir, "textract.txt"), "w", encoding="utf-8") as f:
			f.write(text)
	except Exception as e:
		print(f"❌ Textract failed on {base_filename}: {e}")

def main():
	if not os.path.exists(RESULTS_DIR):
		os.makedirs(RESULTS_DIR)

	files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jp2', '.tif', '.tiff', '.png', '.jpg', '.jpeg'))]

	for file in files:
		full_path = os.path.join(IMAGE_DIR, file)
		process_image(full_path)

if __name__ == "__main__":
	main()
