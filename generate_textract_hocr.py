import os
import json
import subprocess
from PIL import Image, ImageDraw
from lxml import etree

def convert_jp2_to_jpeg(input_path, output_path):
	if not os.path.exists(output_path):
		subprocess.run([
			"convert", input_path,
			"-resize", "100%",
			"-strip",
			"-quality", "100",
			output_path
		], check=True)
	return output_path

def textract_to_hocr_and_preview(textract_json, image_path, hocr_output_path, preview_output_path):
	img = Image.open(image_path).convert("RGB")
	width, height = img.size  # Use actual image size
	doc = etree.Element("html", attrib={
		"xmlns": "http://www.w3.org/1999/xhtml",
		"lang": "en"
	})
	head = etree.SubElement(doc, "head")
	etree.SubElement(head, "title").text = "Textract hOCR Output"
	etree.SubElement(head, "meta", attrib={
		"http-equiv": "Content-Type",
		"content": "text/html;charset=utf-8"
	})
	etree.SubElement(head, "meta", attrib={"name": "ocr-system", "content": "Amazon Textract"})

	body = etree.SubElement(doc, "body")
	page_div = etree.SubElement(body, "div", attrib={
		"class": "ocr_page",
		"id": "page_1",
		"title": f"image bbox 0 0 {width} {height}"
	})

	draw = ImageDraw.Draw(img)

	for block in textract_json.get("Blocks", []):
		if block.get("BlockType") == "LINE":
			bb = block["Geometry"]["BoundingBox"]
			left = int(bb["Left"] * width)
			top = int(bb["Top"] * height)
			right = int((bb["Left"] + bb["Width"]) * width)
			bottom = int((bb["Top"] + bb["Height"]) * height)

			span = etree.SubElement(page_div, "span", attrib={
				"class": "ocr_line",
				"title": f"bbox {left} {top} {right} {bottom}"
			})
			span.text = block.get("Text", "")
			draw.rectangle([left, top, right, bottom], outline="red", width=2)

	tree = etree.ElementTree(doc)
	tree.write(hocr_output_path, pretty_print=True, encoding="utf-8", method="html")
	img.save(preview_output_path)

def process_all_results(results_dir, images_dir):
	for folder in os.listdir(results_dir):
		folder_path = os.path.join(results_dir, folder)
		if not os.path.isdir(folder_path):
			continue

		json_path = os.path.join(folder_path, "textract.json")
		if not os.path.exists(json_path):
			continue

		image_base = folder + ".jp2"
		image_path = os.path.join(images_dir, image_base)
		jpeg_path = image_path.replace(".jp2", ".jpg")

		if not os.path.exists(image_path):
			print(f"⚠️ Skipping {folder}: JP2 image not found")
			continue

		convert_jp2_to_jpeg(image_path, jpeg_path)

		with open(json_path, "r", encoding="utf-8") as f:
			extract_data = json.load(f)

		hocr_out = os.path.join(folder_path, "textract.hocr")
		preview_out = os.path.join(folder_path, "textract_preview.jpg")

		print(f"📍 Generating hOCR and preview for {folder}")
		textract_to_hocr_and_preview(
			textract_json=extract_data,
			image_path=jpeg_path,
			hocr_output_path=hocr_out,
			preview_output_path=preview_out
		)

# Example usage:
process_all_results("results", "test_images")
