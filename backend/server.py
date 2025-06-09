from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import groq
import asyncio
from bson import ObjectId
import json

# Custom JSON encoder for MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Groq client initialization
GROQ_API_KEY = "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"
groq_client = groq.Groq(api_key=GROQ_API_KEY)

# Create the main app without a prefix
app = FastAPI(title="Alpha AI Search Engine")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    search_type: str = Field(default="general")  # general, product, hotel, restaurant
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class SearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str
    search_type: str
    suggestions: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str

class SearchHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str
    search_type: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# AI Search prompts with advanced formatting for different types
SEARCH_PROMPTS = {
    "general": """You are Alpha, an advanced AI search assistant. Provide beautifully formatted, structured responses using markdown formatting.

    Query: {query}
    
    Format your response using this structure based on query type:

    **For Conceptual/Educational Queries:**
    # [Main Topic]
    
    ## Quick Answer
    🎯 [One-sentence explanation]
    
    ## Key Concepts
    - [Important point 1]
    - [Important point 2]
    - [Important point 3]
    
    ## Real-World Applications
    [Practical examples with specific details]
    
    ## Deep Dive
    [Technical details for interested readers]
    
    **For How-To/Tutorial Queries:**
    # [Tutorial Title]
    
    ## Quick Start
    ⚡ [One-line summary or key command]
    
    ## Step-by-Step Guide
    1. **First Step**
       - [Action required]
       - *Why:* [Brief explanation]
    
    2. **Second Step**
       - [Action required]
       - *Why:* [Brief explanation]
    
    ## ⚠️ Common Issues
    - [Troubleshooting tip 1]
    - [Troubleshooting tip 2]
    
    ## 🎯 Next Steps
    - [Recommended action 1]
    - [Recommended action 2]
    
    **For News/Updates:**
    # [Topic] - Latest Updates
    
    ## 🔥 Key Highlights
    - [Important development 1]
    - [Important development 2]
    
    ## 📈 Trends & Analysis
    [Data-backed insights]
    
    ## 💡 What This Means
    [Future implications]
    
    Always use appropriate emojis, headers, and bullet points to make responses visually appealing and easy to scan.""",
    
    "product": """You are Alpha, a product search specialist. Use this structured format for product searches:

    Query: {query}
    
    # [Product Category] - Best Options 2025
    
    ## 🏆 Top Picks at a Glance
    - **Best Overall:** [Product Name] - [Key reason]
    - **Best Value:** [Product Name] - [Key reason]  
    - **Premium Choice:** [Product Name] - [Key reason]
    
    ## Detailed Reviews
    
    ### [Product 1 Name]
    **Price Range:** [Price]
    **Pros:**
    ✅ [Advantage 1]
    ✅ [Advantage 2]
    ✅ [Advantage 3]
    
    **Cons:**
    ❌ [Limitation 1]
    ❌ [Limitation 2]
    
    ### [Product 2 Name]
    **Price Range:** [Price]
    **Pros:**
    ✅ [Advantage 1]
    ✅ [Advantage 2]
    ✅ [Advantage 3]
    
    **Cons:**
    ❌ [Limitation 1]
    ❌ [Limitation 2]
    
    ## 💰 Price Categories
    - **Budget ($X-Y):** [Recommendations]
    - **Mid-Range ($X-Y):** [Recommendations]
    - **Premium ($X+):** [Recommendations]
    
    ## 💡 Pro Tips & Considerations
    - [Buying advice 1]
    - [Buying advice 2]
    - [Where to find deals]
    
    ## 🛒 Where to Buy
    - [Legitimate retailer recommendations]
    - [Best deal sources]
    
    Focus on legitimate, verified options with real pricing and current availability.""",
    
    "hotel": """You are Alpha, a travel and accommodation specialist. Use this structured format for hotel searches:

    Query: {query}
    
    # Hotels in [Location] - Top Recommendations
    
    ## 🏨 Quick Picks
    - **Luxury:** [Hotel Name] - [Key feature]
    - **Best Value:** [Hotel Name] - [Key feature]
    - **Business Travel:** [Hotel Name] - [Key feature]
    
    ## Detailed Recommendations
    
    ### [Hotel 1 Name]
    **Location:** [Specific area/district]
    **Price Range:** [Per night estimate]
    **Star Rating:** ⭐⭐⭐⭐⭐
    
    **Highlights:**
    ✨ [Standout feature 1]
    ✨ [Standout feature 2]
    ✨ [Standout feature 3]
    
    **Amenities:**
    - [Key amenity 1]
    - [Key amenity 2]
    - [Key amenity 3]
    
    ### [Hotel 2 Name]
    **Location:** [Specific area/district]
    **Price Range:** [Per night estimate]
    **Star Rating:** ⭐⭐⭐⭐
    
    **Highlights:**
    ✨ [Standout feature 1]
    ✨ [Standout feature 2]
    ✨ [Standout feature 3]
    
    ## 💰 Budget Breakdown
    - **Luxury ($X+/night):** [Options]
    - **Mid-Range ($X-Y/night):** [Options]
    - **Budget ($X-Y/night):** [Options]
    
    ## 📅 Booking Tips
    - **Best Time to Book:** [Timing advice]
    - **Deal Sources:** [Legitimate booking platforms]
    - **Cancellation:** [Policy recommendations]
    
    ## 🗺️ Location Insights
    - [Area advantages]
    - [Transportation options]
    - [Nearby attractions]
    
    Focus on verified guest reviews and current availability.""",
    
    "restaurant": """You are Alpha, a dining and restaurant specialist. Use this structured format for restaurant searches:

    Query: {query}
    
    # [Cuisine/Area] Restaurants - Top Dining Spots
    
    ## 🍽️ Must-Try Restaurants
    - **Fine Dining:** [Restaurant Name] - [Signature dish]
    - **Best Value:** [Restaurant Name] - [Specialty]
    - **Local Favorite:** [Restaurant Name] - [What makes it special]
    
    ## Detailed Reviews
    
    ### [Restaurant 1 Name]
    **Cuisine:** [Type]
    **Price Range:** [$ symbols or range]
    **Rating:** ⭐⭐⭐⭐⭐
    
    **Signature Dishes:**
    🍽️ [Dish 1] - [Description]
    🍽️ [Dish 2] - [Description]
    🍽️ [Dish 3] - [Description]
    
    **Atmosphere:** [Description]
    **Best For:** [Occasion type]
    
    ### [Restaurant 2 Name]
    **Cuisine:** [Type]
    **Price Range:** [$ symbols or range]
    **Rating:** ⭐⭐⭐⭐
    
    **Signature Dishes:**
    🍽️ [Dish 1] - [Description]
    🍽️ [Dish 2] - [Description]
    
    ## 💰 Price Categories
    - **Fine Dining ($$$+):** [High-end options]
    - **Casual Dining ($$):** [Mid-range options]
    - **Quick Bites ($):** [Affordable options]
    
    ## 📞 Reservation Tips
    - **Advance Booking:** [How far ahead]
    - **Peak Times:** [When to avoid/prefer]
    - **Special Offers:** [Happy hours, deals]
    
    ## 🚗 Location & Access
    - [Address/area information]
    - [Parking availability]
    - [Public transport options]
    
    ## 💡 Insider Tips
    - [Local recommendations]
    - [Best dishes to order]
    - [Timing advice]
    
    Focus on authentic reviews and current operating status."""
}

async def get_ai_response(query: str, search_type: str = "general"):
    """Get AI response using Groq with optimized prompts"""
    try:
        prompt = SEARCH_PROMPTS.get(search_type, SEARCH_PROMPTS["general"]).format(query=query)
        
        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Alpha, an intelligent search assistant focused on providing fast, accurate, and practical information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-70b-8192",  # Using fast Groq model
            temperature=0.3,  # Lower temperature for more focused results
            max_tokens=1024,
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

def generate_suggestions(query: str, search_type: str) -> List[str]:
    """Generate relevant follow-up suggestions"""
    base_suggestions = {
        "general": [
            "Tell me more about this topic",
            "What are the latest developments?",
            "How does this compare to alternatives?"
        ],
        "product": [
            "Show me budget alternatives",
            "What are the top brands?",
            "Where can I find the best deals?"
        ],
        "hotel": [
            "Show me luxury options",
            "What about budget-friendly hotels?",
            "Best areas to stay in this city"
        ],
        "restaurant": [
            "Show me fine dining options",
            "What about casual dining?",
            "Best local cuisine recommendations"
        ]
    }
    return base_suggestions.get(search_type, base_suggestions["general"])

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Alpha AI Search Engine API"}

@api_router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Main search endpoint"""
    try:
        # Determine search type if not specified
        query_lower = request.query.lower()
        if request.search_type == "general":
            if any(word in query_lower for word in ["buy", "product", "price", "purchase", "best", "recommend"]):
                if any(word in query_lower for word in ["hotel", "stay", "accommodation", "booking"]):
                    request.search_type = "hotel"
                elif any(word in query_lower for word in ["restaurant", "eat", "food", "dining", "meal"]):
                    request.search_type = "restaurant"
                else:
                    request.search_type = "product"
        
        # Get AI response
        ai_response = await get_ai_response(request.query, request.search_type)
        
        # Generate suggestions
        suggestions = generate_suggestions(request.query, request.search_type)
        
        # Create response
        search_response = SearchResponse(
            query=request.query,
            response=ai_response,
            search_type=request.search_type,
            suggestions=suggestions,
            session_id=request.session_id
        )
        
        # Save to database
        search_history = SearchHistory(
            id=search_response.id,
            query=request.query,
            response=ai_response,
            search_type=request.search_type,
            session_id=request.session_id
        )
        
        await db.search_history.insert_one(search_history.dict())
        
        return search_response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Search processing failed")

@api_router.get("/search/history/{session_id}")
async def get_search_history(session_id: str, limit: int = 10):
    """Get search history for a session"""
    try:
        cursor = db.search_history.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit)
        
        # Convert MongoDB documents to Python dictionaries and handle ObjectId
        history = []
        async for doc in cursor:
            # Convert ObjectId to string
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            history.append(doc)
        
        return {"history": history}
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

@api_router.get("/search/suggestions")
async def get_search_suggestions():
    """Get popular search suggestions"""
    suggestions = [
        "Best laptops for programming in 2025",
        "Top hotels in Tokyo with good reviews",
        "Best Italian restaurants in New York",
        "Affordable smartphones with great cameras",
        "Hotels with pool near downtown Los Angeles",
        "Best coffee shops for remote work",
        "Gaming headsets under $100",
        "Luxury hotels in Paris with Eiffel Tower view"
    ]
    return {"suggestions": suggestions}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
