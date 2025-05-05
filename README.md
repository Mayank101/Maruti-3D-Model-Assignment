# Car Model Generator

## Description
Generate and refine 3D models (Spoiler or Brake) using Meshy's text-to-3D API. Dimensions and texture details are integrated via prompt.

## Setup
1. Install requirements:
```
pip install -r requirements.txt
```

2. Copy the environment variables to `.env` and paste your Meshy API key.

3. Run:
```
streamlit run app.py
```

## Code Working

Code connects with the **Meshy Text-to-3D API** and follows this flow:

### 1. Prompt Generation
- Based on user input (part type + dimensions) from radio button and sliders, the code creates a descriptive natural language prompt
  ```
  e.g., A realistic carbon fiber spoiler, 1.2 meters long, 0.3 meters wide, ...
  ```

### 2. Meshy Preview Generation
- Sends the prompt to Meshy's `/text-to-3d` API
- Meshy returns a task ID
- Code then polls every 2 seconds until Meshy finishes the preview model

### 3. Refinement
- Once the preview is ready, the code automatically calls the **refine API**
- This step adds realistic textures and material finishes (PBR)

### 4. 3D Viewer + Download
- The `.glb` file from Meshy is:
  - Downloaded
  - Embedded in-browser using `model-viewer`
