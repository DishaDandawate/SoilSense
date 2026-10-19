from django.shortcuts import render, redirect
import pandas as pd
import plotly.express as px
import datetime, math, os
from django.shortcuts import render, redirect

from .models import Location
from django.views.decorators.csrf import csrf_protect

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .models import SoilAnalysis

from itertools import zip_longest
from google import genai
from PIL import Image
import datetime

import os
import json

from PIL import Image, UnidentifiedImageError

from django.shortcuts import render
import os
import json

from PIL import Image, UnidentifiedImageError
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

SOIL_ANALYSIS_PROMPT = """
You are an AI assistant for preliminary visual soil assessment.

Analyze the uploaded photograph and return ONLY valid JSON with
the exact fields and value types defined below.

Rules:
1. Analyze only what is reasonably visible in the photograph.
2. Estimate a broad soil category only when visual evidence supports it.
3. Distinguish direct visual observations from uncertain inferences.
4. Never invent exact pH, NPK, salinity, nutrient concentrations,
   moisture percentages, or laboratory measurements.
5. For properties that cannot be determined from the image, return null.
6. Do not diagnose contamination or claim that soil is safe for crops
   based on a photograph.
7. Recommendations must be cautious and suitable for preliminary
   assessment, not a substitute for laboratory testing.
8. If the image does not show soil clearly, say so in the JSON.
9. Do not claim certainty or provide unsupported confidence percentages.

Return a JSON object with these exact fields:

{
  "image_suitable": true,
  "soil_type_estimate": "string or null",
  "visible_color": "string or null",
  "visible_texture": "string or null",
  "visible_moisture": "string or null",
  "visible_organic_matter": "string or null",
  "observations": ["string"],
  "possible_uses": ["string"],
  "limitations": ["string"],
  "recommended_tests": ["string"],
  "next_steps": ["string"]
}

Use null for unknown individual values. Use false for image_suitable
when the image is not suitable for soil assessment.
Do not add, remove, or rename fields.
"""


def get_soil_analysis(image):
    api_key = os.getenv("API_KEY", "")
    model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")

    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    if not model_name:
        raise ValueError("Gemini model is not configured.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=[
            SOIL_ANALYSIS_PROMPT,
            image,
        ],
        config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    )

    if not response.text:
        raise ValueError("The AI returned an empty response.")

    result = json.loads(response.text)

    required_fields = [
        "image_suitable",
        "soil_type_estimate",
        "visible_color",
        "visible_texture",
        "visible_moisture",
        "visible_organic_matter",
        "observations",
        "possible_uses",
        "limitations",
        "recommended_tests",
        "next_steps",
    ]

    if not isinstance(result, dict):
        raise ValueError("Invalid AI response format.")

    if any(field not in result for field in required_fields):
        raise ValueError("The AI response is missing required fields.")

    for field in (
        "observations",
        "possible_uses",
        "limitations",
        "recommended_tests",
        "next_steps",
    ):
        if not isinstance(result[field], list):
            raise ValueError("Invalid list in AI response.")

    if not isinstance(result["image_suitable"], bool):
        raise ValueError("Invalid image suitability value.")

    return result


@require_http_methods(["GET", "POST"])
def soil_analysis_view(request):
    if request.method == "GET":
        return render(request, "soil_analysis.html")

    uploaded_file = request.FILES.get("soil_image")

    if not uploaded_file:
        return render(request, "soil_analysis.html", {
            "error": "Please upload a soil image."
        })

    allowed_types = {"image/jpeg", "image/png", "image/webp"}

    if uploaded_file.content_type not in allowed_types:
        return render(request, "soil_analysis.html", {
            "error": "Upload a JPG, PNG or WEBP image."
        })

    # Limit uploads to 8 MB.
    if uploaded_file.size > 8 * 1024 * 1024:
        return render(request, "soil_analysis.html", {
            "error": "Image size must not exceed 8 MB."
        })

    try:
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as source:
            source.verify()

        uploaded_file.seek(0)

        with Image.open(uploaded_file) as source:
            source.load()
            image = source.convert("RGB")

        result = get_soil_analysis(image)

        if result.get("image_suitable"):
            uploaded_file.seek(0)

            SoilAnalysis.objects.create(
                user=request.user if request.user.is_authenticated else None,
                image=uploaded_file,
                soil_type_estimate=result.get("soil_type_estimate"),
                analysis_result=result,
                latitude=request.POST.get("latitude") or None,
                longitude=request.POST.get("longitude") or None,
            )

        return render(request, "soil_analysis.html", {
            "result": result,
        })

    except (UnidentifiedImageError, OSError):
        return render(request, "soil_analysis.html", {
            "error": "The uploaded file is not a valid image."
        })

    except Exception as e:
        # Log the actual exception privately in production.
        print(e)
        return render(request, "soil_analysis.html", {
            "error": (
                "Soil analysis could not be completed. "
                "Please try again later."
            )
        })


@csrf_protect
def homeView(request):
    if request.method == 'POST':
        name = request.POST.get('place')
        desc = request.POST.get('description')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        user = request.user

        if 'image' in request.FILES:
            file = request.FILES['image']

            temp_path = os.path.join('C:\\Users\\harsh\\OneDrive\\Desktop\\SEM4\\EDAI\\static\\temp', file.name)
            with open(temp_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            try:
                image = Image.open(temp_path)
                image_format = image.format.lower()
                print(image.format)
                if image_format in ['png','jpg','jpeg']:
                    #model = YOLO("edai/b.pt")
                    model = None
                    print("Before result")
                    results = model.predict(source=image, stream=True, imgsz=512, show=True)
                    print("After result")
                    names = model.names
                    s=''
                    flag = False
                    print(image_format in ['PNG','JPG','JPEG'])

                    for r in results:
                        for c in r.boxes.cls:
                            s = s + names[int(c)]

                        if "Dirty" in s and "Clean" not in s:
                            flag = True
                            print(s)
                            s = ''
                    
                    if flag:
                        try:
                            Location.objects.create(user=user, place=name, latitude=latitude, longitude=longitude, image=file, description=desc, date=datetime.date.today())
                        except Exception as e:
                            print(e)
                        return render(request, 'home.html', {'showAlert':False, 'success':True, 'user':checkUser(request)})
                    else:
                        return render(request, 'home.html', {'showAlert':False, 'failure':True, 'user':checkUser(request)})
                else:
                    return render(request, 'home.html', {'showAlert':True, 'success':True, 'user':checkUser(request)})
            
            except Exception as e:
                print("in except: ", e)
                if file.name.split('.')[-1] == 'mp4':
                    model = YOLO("edai/b.pt")
                    results = model.predict(source=temp_path, stream=True, imgsz=512, show=False)
                    names = model.names
                    s=''
                    flag = False

                    for r in results:
                        for c in r.boxes.cls:
                            s = s + names[int(c)]

                        if "Dirty" in s and "Clean" not in s:
                            flag = True
                            print(s)
                            s = ''
                    
                    if flag:
                        Location.objects.create(user=user, place=name, latitude=latitude, longitude=longitude, video=file, description=desc, date=datetime.date.today)
                        return render(request, 'home.html', {'showAlert':False, 'success':True, 'user':checkUser(request)})
                    else:
                        return render(request, 'home.html', {'showAlert':False, 'failure':True, 'user':checkUser(request)})
                else:
                    return render(request, 'home.html', {'showAlert':True, 'success':True, 'user':checkUser(request)})

        return redirect('home')

    return render(request, 'home.html', {'showAlert':False, 'user':checkUser(request)})


def mapView(request):
    # Fetch soil analysis records instead of Location records
    soil_records = SoilAnalysis.objects.all()

    locations = []
    longitudes = []
    latitudes = []

    for record in soil_records:
        # Use coordinates from the soil record
        if record.latitude is not None and record.longitude is not None:
            locations.append(
                record.soil_type_estimate or "Unknown Soil Type"
            )
            longitudes.append(float(record.longitude))
            latitudes.append(float(record.latitude))

    data = {
        "location": locations,
        "lon": longitudes,
        "lat": latitudes,
    }

    df = pd.DataFrame(data)

    if not df.empty:
        fig = px.scatter_geo(
            df,
            lon="lon",
            lat="lat",
            text="location",
            scope="asia",
            title="Soil Analysis Locations in India",
        )

        fig.update_geos(projection_type="natural earth")
        fig.update_layout(height=650)

        plot_html = fig.to_html(full_html=True)
    else:
        plot_html = (
            "<p>No soil analysis records with valid coordinates "
            "are available to display on the map.</p>"
        )

    return render(
        request,
        "map.html",
        {
            "plot_html": plot_html,
            "user": checkUser(request),
        },
    )


@csrf_protect
def feedView(request):
    if request.method == 'POST':
        long = request.POST.get('long')
        lat = request.POST.get('lat')

        res = Location.objects.all()

        locations = []
        for item in res:
            if haversine(item.latitude,item.longitude,float(lat),float(long)) <= 1000:
                diff = datetime.datetime.now().date() - item.date
                item.date_diff = diff.days
                locations.append(item)

        i = 0
        length = len(locations)
        l1, l2, l3 = [], [], []

        for loc in locations:
            if i < length/3:
                l1.append(loc)
            elif i< (2*length)/3:
                l2.append(loc)
            else:
                l3.append(loc)
            i += 1

        data = zip_longest(l1,l2,l3)
        return render(request, 'feed.html', {'data':data, 'post':True, 'user':checkUser(request)})
    
    else:
        return render(request, 'feed.html', {'post':False, 'user':checkUser(request)})


def contactView(request):
    return render(request, 'contact.html', {'user':checkUser(request)})


def haversine(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c
    return distance


def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not User.objects.filter(username=email).exists():
            print("No such user")
            return redirect("login")
        
        user = authenticate(username=email,password=password)

        if user is None:
            print("No such user wrong")
            return redirect("login")
        else:
            login(request,user)
            return redirect('soil_analysis')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('soil_analysis')


def register(request):
    if request.method == "POST":
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = User.objects.filter(username=email)

        if user.exists():
            return redirect("register")

        user = User.objects.create(first_name=fname, last_name=lname, username=email)
        user.set_password(password)
        user.save()
        return redirect("login")

    return render(request, 'register.html')


def checkUser(request):
    try:
        user = request.user.first_name
    except:
        user = ''
    return user

def test(request):
    model = YOLO("edai/b.pt")
    results = model.predict(source="C:/Users/harsh/OneDrive/Desktop/SEM4/EDAI/static/h.jpg", stream=True, imgsz=512, show=False)
    names = model.names
    s=''

    for r in results:
        for c in r.boxes.cls:
            s = s + names[int(c)]

        if ("helmet" in s or "vest" in s or "human" in s):
            print(s)
            s = ''

        else:
            print("No gears detected")
    return render(request, 'test.html')