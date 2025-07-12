from transformers import GPT2LMHeadModel, GPT2Tokenizer
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger
import torch
import asyncio
from functools import lru_cache

logger = get_logger("llm_service")


class LLMService:
    """
    LLM Service using GPT-2 from HuggingFace for generating responses
    based on user messages and previous conversation context.
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = 512
        self.is_initialized = False
    
    async def initialize_model(self):
        """
        Initialize GPT-2 model and tokenizer asynchronously.
        """
        try:
            if self.is_initialized:
                logger.info("LLM model already initialized")
                return
            
            logger.info("Initializing GPT-2 model and tokenizer...")
            
            # Load pre-trained GPT-2 model and tokenizer
            model_name = "gpt2"
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self.model = GPT2LMHeadModel.from_pretrained(model_name)
            
            # Add pad token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Move model to appropriate device
            self.model.to(self.device)
            self.model.eval()
            
            self.is_initialized = True
            logger.info(f"GPT-2 model initialized successfully on device: {self.device}")
            
        except Exception as e:
            logger.error(f"Error initializing GPT-2 model: {str(e)}")
            raise
    
    def _format_context(self, system_messages: List[Dict[str, str]]) -> str:
        """
        Format previous conversation context into a readable string.        
        Args:
            system_messages: List of previous user-system message pairs
        Returns:
            str: Formatted context string
        """
        if not system_messages:
            return ""
        
        context = "Previous conversation context:\n"
        for i, msg_pair in enumerate(system_messages, 1):
            user_msg = msg_pair.get("user", "")
            system_msg = msg_pair.get("system", "")
            
            if user_msg and system_msg:
                context += f"\nConversation {i}:\n"
                context += f"User: {user_msg}\n"
                context += f"Assistant: {system_msg}\n"
        
        return context + "\n"
    
    def _create_prompt(self, user_message: str, system_messages: List[Dict[str, str]]) -> str:
        """
        Create a comprehensive prompt using the user message and context.
        Args:
            user_message: Current user message
            system_messages: Previous conversation context
            
        Returns:
            str: Complete prompt for GPT-2
        """
        # Format context from previous conversations
        context = self._format_context(system_messages)
        
        # Sample prompt template
        prompt = '''You are a helpful chat assistant. 
        You are given a conversation history and a current user question. 
        You need to generate a response to the user question based on the conversation history. 
        The response should be formal and in the same language as the user question. 
        Avoid any other text or information in the response.'''
        
        # Build the complete prompt
        full_prompt = f"""{prompt}, Previous Converstion History : {context}, Current user question: {user_message}, Assistant response:"""
        
        return full_prompt
    
    async def generate_response(
        self, 
        user_message: str, 
        system_messages: List[Dict[str, str]] = None,
        max_new_tokens: int = 150,
        temperature: float = 0.7,
        do_sample: bool = True,
        top_k: int = 50,
        top_p: float = 0.95
    ) -> str:
        """
        Generate a response using GPT-2 based on user message and context.
        
        Args:
            user_message: Current user message
            system_messages: Previous conversation context
            max_new_tokens: Maximum number of new tokens to generate
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            top_k: Top-k sampling parameter
            top_p: Top-p sampling parameter
            
        Returns:
            str: Generated response
        """
        try:
            # Initialize model if not already done
            if not self.is_initialized:
                await self.initialize_model()
            
            # Prepare system messages
            if system_messages is None:
                system_messages = []
            
            # Create the prompt
            prompt = self._create_prompt(user_message, system_messages)
            
            logger.info(f"Generating response for user message: {user_message[:50]}...")
            logger.info(f"Using {len(system_messages)} previous conversations as context")
            
            # Tokenize the prompt
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors="pt", 
                max_length=self.max_length, 
                truncation=True
            ).to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=do_sample,
                    top_k=top_k,
                    top_p=top_p,
                    pad_token_id=self.tokenizer.eos_token_id,
                    attention_mask=torch.ones(inputs.shape, device=self.device)
                )
            
            # Decode the response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (remove the prompt)
            response = full_response[len(prompt):].strip()
            
            # Clean up the response
            response = self._clean_response(response)
            
            logger.info(f"Generated response length: {len(response)} characters")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while processing your message. Please try again."
    
    def _clean_response(self, response: str) -> str:
        """
        Clean and format the generated response.
        Args:
            response: Raw generated response
        Returns:
            str: Cleaned response
        """
        # Remove extra whitespace
        response = response.strip()
        
        # Stop at first occurrence of these patterns that might indicate end of response
        stop_patterns = ["\n\nUser:", "\nUser:", "\n\nCurrent user", "\nCurrent user"]
        for pattern in stop_patterns:
            if pattern in response:
                response = response.split(pattern)[0].strip()
        
        # If response is empty or too short, provide a default
        if not response or len(response) < 10:
            response = "I understand your question. Let me provide you with a helpful response based on our conversation."
        
        return response
    
    async def generate_contextual_response(
        self, 
        user_message: str, 
        system_messages: List[Dict[str, str]] = None
    ) -> str:
        """
        Simplified method for generating contextual responses.
        This is the main method that will be called from the celery worker.
        
        Args:
            user_message: Current user message
            system_messages: Previous conversation context
            
        Returns:
            str: Generated response
        """
        return await self.generate_response(
            user_message=user_message,
            system_messages=system_messages or [],
            max_new_tokens=100,
            temperature=0.8,
            do_sample=True,
            top_k=40,
            top_p=0.9
        )


# Global instance
llm_service = LLMService()


async def get_llm_response(user_message: str, system_messages: List[Dict[str, str]] = None) -> str:
    """
    Convenience function to get LLM response.
    This is the main function that will be called from the celery worker.
    
    Args:
        user_message: Current user message
        system_messages: Previous conversation context
        
    Returns:
        str: Generated response
    """
    try:
        return await llm_service.generate_contextual_response(user_message, system_messages)
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        return "I apologize, but I encountered an error while processing your message. Please try again."
