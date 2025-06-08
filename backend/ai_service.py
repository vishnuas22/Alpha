import openai
import anthropic
from typing import List, Dict, Any, Optional, AsyncIterator
import tiktoken
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings
from models import ModelName, Message, MessageType

logger = structlog.get_logger()

class AIService:
    def __init__(self):
        # Initialize AI clients
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not provided")
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            self.anthropic_client = None
            logger.warning("Anthropic API key not provided")
        
        # Model mappings
        self.model_mappings = {
            ModelName.ALPHA_ORIGIN: "gpt-3.5-turbo",
            ModelName.ALPHA_PRIME: "gpt-4-turbo",
            ModelName.GPT_4: "gpt-4",
            ModelName.GPT_4_TURBO: "gpt-4-turbo",
            ModelName.GPT_3_5_TURBO: "gpt-3.5-turbo",
            ModelName.CLAUDE_3_OPUS: "claude-3-opus-20240229",
            ModelName.CLAUDE_3_SONNET: "claude-3-sonnet-20240229"
        }
        
        # Token limits per model
        self.token_limits = {
            "gpt-3.5-turbo": 4096,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000
        }
    
    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in text for a given model"""
        try:
            if "claude" in model:
                # Approximate token count for Claude (roughly 4 chars per token)
                return len(text) // 4
            else:
                # Use tiktoken for OpenAI models
                encoding = tiktoken.encoding_for_model(model)
                return len(encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback approximation
            return len(text) // 4
    
    def format_messages_for_openai(self, messages: List[Message], system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Format messages for OpenAI API"""
        formatted_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Convert messages
        for message in messages:
            role = "user" if message.type == MessageType.USER else "assistant"
            formatted_messages.append({
                "role": role,
                "content": message.content
            })
        
        return formatted_messages
    
    def format_messages_for_claude(self, messages: List[Message], system_prompt: Optional[str] = None) -> tuple:
        """Format messages for Claude API"""
        formatted_messages = []
        
        # Claude doesn't use system messages in the messages array
        for message in messages:
            role = "user" if message.type == MessageType.USER else "assistant"
            formatted_messages.append({
                "role": role,
                "content": message.content
            })
        
        return formatted_messages, system_prompt or ""
    
    def truncate_messages_to_fit_context(self, messages: List[Message], model: str, system_prompt: Optional[str] = None, max_tokens: int = 2000) -> List[Message]:
        """Truncate messages to fit within context window"""
        model_key = self.model_mappings.get(model, model)
        context_limit = self.token_limits.get(model_key, 4096)
        
        # Reserve tokens for response and system prompt
        available_tokens = context_limit - max_tokens
        if system_prompt:
            available_tokens -= self.count_tokens(system_prompt, model_key)
        
        # Start from the most recent messages and work backwards
        truncated_messages = []
        current_tokens = 0
        
        for message in reversed(messages):
            message_tokens = self.count_tokens(message.content, model_key)
            if current_tokens + message_tokens <= available_tokens:
                truncated_messages.insert(0, message)
                current_tokens += message_tokens
            else:
                break
        
        return truncated_messages
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response_openai(
        self, 
        messages: List[Message], 
        model: ModelName,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        model_name = self.model_mappings.get(model, "gpt-3.5-turbo")
        
        # Truncate messages to fit context
        truncated_messages = self.truncate_messages_to_fit_context(
            messages, model_name, system_prompt, max_tokens
        )
        
        # Format messages
        formatted_messages = self.format_messages_for_openai(truncated_messages, system_prompt)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=model_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return {"stream": response}
            else:
                return {
                    "content": response.choices[0].message.content,
                    "model": model_name,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "finish_reason": response.choices[0].finish_reason
                }
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_response_claude(
        self, 
        messages: List[Message], 
        model: ModelName,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate response using Claude API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        model_name = self.model_mappings.get(model, "claude-3-sonnet-20240229")
        
        # Truncate messages to fit context
        truncated_messages = self.truncate_messages_to_fit_context(
            messages, model_name, system_prompt, max_tokens
        )
        
        # Format messages
        formatted_messages, system = self.format_messages_for_claude(truncated_messages, system_prompt)
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=formatted_messages,
                stream=stream
            )
            
            if stream:
                return {"stream": response}
            else:
                return {
                    "content": response.content[0].text,
                    "model": model_name,
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                    "finish_reason": response.stop_reason
                }
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def generate_response(
        self, 
        messages: List[Message], 
        model: ModelName,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate AI response using appropriate provider"""
        try:
            if model in [ModelName.CLAUDE_3_OPUS, ModelName.CLAUDE_3_SONNET]:
                return await self.generate_response_claude(
                    messages, model, system_prompt, temperature, max_tokens, stream
                )
            else:
                return await self.generate_response_openai(
                    messages, model, system_prompt, temperature, max_tokens, stream
                )
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            # Return a fallback response
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                "model": "fallback",
                "tokens_used": 0,
                "finish_reason": "error"
            }
    
    async def generate_stream_response(
        self, 
        messages: List[Message], 
        model: ModelName,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate streaming AI response"""
        try:
            response = await self.generate_response(
                messages, model, system_prompt, temperature, max_tokens, stream=True
            )
            
            stream = response["stream"]
            
            if model in [ModelName.CLAUDE_3_OPUS, ModelName.CLAUDE_3_SONNET]:
                # Handle Claude streaming
                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        yield {
                            "type": "chunk",
                            "content": chunk.delta.text,
                            "finish_reason": None
                        }
                    elif chunk.type == "message_stop":
                        yield {
                            "type": "end",
                            "content": "",
                            "finish_reason": "stop"
                        }
            else:
                # Handle OpenAI streaming
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield {
                            "type": "chunk",
                            "content": chunk.choices[0].delta.content,
                            "finish_reason": None
                        }
                    
                    if chunk.choices and chunk.choices[0].finish_reason:
                        yield {
                            "type": "end",
                            "content": "",
                            "finish_reason": chunk.choices[0].finish_reason
                        }
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "type": "error",
                "content": "An error occurred while generating the response.",
                "error": str(e)
            }
    
    async def generate_title(self, first_message: str) -> str:
        """Generate a title for a chat based on the first message"""
        try:
            title_prompt = f"Generate a short, descriptive title (max 50 characters) for a conversation that starts with: '{first_message[:200]}'"
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You generate short, descriptive titles for conversations. Keep titles under 50 characters and make them descriptive but concise."},
                    {"role": "user", "content": title_prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            title = response.choices[0].message.content.strip()
            # Remove quotes if present
            title = title.strip('"').strip("'")
            
            return title[:50]  # Ensure max length
        
        except Exception as e:
            logger.error(f"Title generation error: {e}")
            return "New Chat"

# Global AI service instance
ai_service = AIService()