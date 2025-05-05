import streamlit as st
import requests
import tempfile
import base64
import time
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit.components.v1 as components


load_dotenv()

# --- CONFIG ---
MESHY_API_KEY = os.getenv("MESHY_API_KEY")
MESHY_API_URL = os.getenv("MESHY_API_URL")


# function to generate preview model
def generate_preview_model(prompt):
    headers = {
        "Authorization": f"Bearer {MESHY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "mode": "preview",
        "prompt": prompt,
        "art_style": "realistic",
        "should_remesh": True
    }
    response = requests.post(MESHY_API_URL, json=data, headers=headers)
    st.write(f"Meshy API Response Code: {response.status_code}")
    st.code(response.text)
    if response.status_code == 200:
        return response.json().get("result")
    st.error("Failed to initiate preview model generation.")
    return None


# function that polls until task is complete
def poll_task(task_id):
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    status_url = f"{MESHY_API_URL}/{task_id}"
    for i in range(45):
        response = requests.get(status_url, headers=headers)
        st.write(f"Polling task... attempt {i+1}")
        if response.status_code == 200:
            result = response.json()
            st.code(result)
            if result.get("status") == "SUCCEEDED":
                resources = result.get("output", {}).get("resources", [])
                if resources:
                    return resources[0].get("url"), task_id
            elif result.get("status") == "FAILED":
                st.error("Task failed.")
                return None, None
        time.sleep(2)
    return None, None


# function to refine the output model with texture
def refine_model(preview_task_id, texture_prompt):
    headers = {
        "Authorization": f"Bearer {MESHY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "mode": "refine",
        "preview_task_id": preview_task_id,
        "enable_pbr": True,
        "texture_prompt": texture_prompt
    }
    response = requests.post(MESHY_API_URL, json=data, headers=headers)
    if response.status_code == 200:
        refine_task_id = response.json().get("result")
        status_url = f"{MESHY_API_URL}/{refine_task_id}"
        for i in range(45):
            status_response = requests.get(status_url, headers=headers)
            st.write(f"Polling refine task... attempt {i+1}")
            if status_response.status_code == 200:
                result = status_response.json()
                st.code(result)
                if result.get("status") == "SUCCEEDED":
                    resources = result.get("output", {}).get("resources", [])
                    if resources:
                        return resources[0].get("url")
                elif result.get("status") == "FAILED":
                    st.error("Refine task failed.")
                    return None
            time.sleep(2)
    st.error("Failed to initiate refine task.")
    return None


# function to show model in viewer
def display_3d_model_from_url(download_url):
    response = requests.get(download_url)
    file_path = tempfile.mktemp(suffix=".glb")
    with open(file_path, "wb") as f:
        f.write(response.content)
    with open(file_path, "rb") as f:
        base64_model = base64.b64encode(f.read()).decode("utf-8")
    html_code = f"""
    <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
    <model-viewer src="data:model/gltf-binary;base64,{base64_model}"
                  alt="3D Model"
                  auto-rotate
                  camera-controls
                  background-color="#FFFFFF"
                  style="width: 100%; height: 500px;">
    </model-viewer>
    """
    components.html(html_code, height=520)
    st.download_button("Download 3D Model (.glb)", open(file_path, "rb"), file_name="model.glb")


# UI 
st.set_page_config(page_title="3D Model Generator for Car", layout="centered")
st.title("Car parts 3D Model Generator")

part_type = st.radio("Choose part type:", ["Spoiler", "Brake"])

if part_type == "Spoiler":
    length = st.slider("Length (meters)", 1.0, 1.6, 1.2, 0.1)
    width = st.slider("Width (meters)", 0.1, 0.5, 0.3, 0.05)
    height = st.slider("Height (meters)", 0.05, 0.3, 0.1, 0.05)

elif part_type == "Brake":
    length = st.slider("Diameter (meters)", 0.22, 0.30, 0.26, 0.01)
    height = st.slider("Thickness (meters)", 0.015, 0.035, 0.025, 0.005)
    width = 0 

if st.button(f"Generate {part_type}"):
    if part_type == "Spoiler":
        prompt = f"A realistic carbon fiber car spoiler, {length} meters long, {width} meters wide, {height} meters tall, aerodynamic with metallic brackets"
    else:
        prompt = f"A realistic disc brake, {length} meters in diameter, {height} meters thick, ventilated, racing style, with metallic texture"

    st.write("Using prompt:")
    st.success(prompt)

    with st.spinner("Generating 3D preview..."):
        preview_task_id = generate_preview_model(prompt)
        if preview_task_id:
            download_url, task_id = poll_task(preview_task_id)
            if download_url:
                st.success("Preview ready. Refining model...")
                refined_url = refine_model(task_id, prompt)
                if refined_url:
                    st.success("Refined 3D Model Ready!")
                    display_3d_model_from_url(refined_url)
                else:
                    st.warning("Showing unrefined preview model.")
                    display_3d_model_from_url(download_url)
            else:
                st.error("Preview generation failed.")