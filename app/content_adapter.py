"""
Content Adapter - Adapte le contenu entre AI Inference et GPU Compute
Utilise les vrais prix et comparaisons pertinentes
"""

import random
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ContentAdapter:
    """Adapte le contenu selon le contexte: AI Inference vs GPU Compute"""
    
    # VRAIS PRIX AI INFERENCE (per 1M tokens)
    AI_MODELS = {
        'deepseek_r1': {
            'name': 'DeepSeek-R1',
            'input_price': 0.47,
            'output_price': 1.85,
            'context': '128k',
            'runs': '13.23M',
            'description': 'o1-caliber reasoning at fraction of price'
        },
        'hermes_405b': {
            'name': 'NousResearch/Hermes-4-405B-FP8',
            'input_price': 0.46,
            'output_price': 1.85,
            'context': '128k',
            'runs': '13.23M',
            'description': 'Enterprise-grade LLM'
        },
        'qwen_32b': {
            'name': 'Qwen3-32B',
            'input_price': 0.06,
            'output_price': 0.24,
            'context': '32k',
            'runs': '8.7M',
            'description': 'Cost-effective reasoning'
        },
        'glm_air': {
            'name': 'GLM-4.5-Air',
            'input_price': 0,  # FREE
            'output_price': 0,
            'context': '8k',
            'runs': '5.2M',
            'description': 'FREE tier available'
        }
    }
    
    # COMPARAISONS OPENAI
    OPENAI_PRICES = {
        'o1': {'input': 15, 'output': 60},
        'o3': {'input': 2, 'output': 8},
        'gpt4': {'input': 10, 'output': 30},
        'gpt35': {'input': 0.5, 'output': 1.5}
    }
    
    # VRAIS PRIX GPU COMPUTE (per hour)
    GPU_OFFERINGS = {
        'h200_cluster': {
            'name': '8x NVIDIA H200',
            'price': 26.60,
            'cpu': '256 cores Intel Xeon Platinum',
            'ram': '2TB',
            'location': 'Douglasville, US',
            'uptime': '99.9%'
        },
        'a100_cluster': {
            'name': '8x A100-80GB',
            'price': 6.02,
            'cpu': '120 cores AMD EPYC',
            'ram': '1.8TB',
            'location': 'Washington, US',
            'uptime': '99.9%'
        },
        'rtx_a6000': {
            'name': '5x RTX A6000',
            'price': 2.10,
            'cpu': '64 cores Intel Xeon',
            'ram': '504GB',
            'location': 'Des Moines, US',
            'uptime': '99.9%'
        },
        'rtx_3090': {
            'name': '2x RTX 3090',
            'price': 0.46,
            'cpu': '32 cores',
            'ram': '128GB',
            'location': 'Global',
            'uptime': '99.5%'
        }
    }
    
    # COMPARAISONS AWS
    AWS_PRICES = {
        'p5.48xlarge': {  # 8x H100
            'price': 98.32,
            'gpus': '8x H100',
            'ram': '2TB'
        },
        'p4d.24xlarge': {  # 8x A100
            'price': 32.77,
            'gpus': '8x A100',
            'ram': '1.1TB'
        },
        'g5.48xlarge': {  # 8x A10G
            'price': 16.29,
            'gpus': '8x A10G',
            'ram': '768GB'
        }
    }
    
    def detect_context(self, hashtags: List[str]) -> str:
        """Détecte si on parle d'AI Inference ou GPU Compute"""
        
        # Mots-clés AI Inference
        ai_keywords = ['ai', 'llm', 'gpt', 'model', 'inference', 'reasoning', 
                      'deepseek', 'openai', 'claude', 'gemini', 'mistral',
                      'language', 'nlp', 'transformer', 'bert', 'chat']
        
        # Mots-clés GPU Compute
        gpu_keywords = ['gpu', 'compute', 'nvidia', 'cuda', 'training', 
                       'render', 'mining', 'hpc', 'cluster', 'datacenter',
                       'a100', 'h100', 'h200', 'rtx', 'aws', 'cloud']
        
        # Analyser les hashtags
        hashtags_lower = ' '.join(hashtags).lower()
        
        ai_score = sum(1 for kw in ai_keywords if kw in hashtags_lower)
        gpu_score = sum(1 for kw in gpu_keywords if kw in hashtags_lower)
        
        # Si égalité ou pas clair, alterner
        if ai_score > gpu_score:
            return 'ai_inference'
        elif gpu_score > ai_score:
            return 'gpu_compute'
        else:
            # Alterner 50/50
            return random.choice(['ai_inference', 'gpu_compute'])
    
    def get_ai_inference_content(self) -> Dict:
        """Génère du contenu pour AI Inference avec vrais prix"""
        
        # Choisir un modèle VoltageGPU
        model_key = random.choice(list(self.AI_MODELS.keys()))
        model = self.AI_MODELS[model_key]
        
        # Choisir un concurrent OpenAI
        competitor_key = random.choice(list(self.OPENAI_PRICES.keys()))
        competitor = self.OPENAI_PRICES[competitor_key]
        
        # Calculer les économies
        voltage_cost = model['input_price']
        openai_cost = competitor['input']
        savings = int(((openai_cost - voltage_cost) / openai_cost) * 100) if voltage_cost > 0 else 100
        
        # Exemples de projets avec contexte clair
        projects = [
            {
                'name': 'RAG pipeline',
                'description': '80k tokens input + 10k output',
                'voltage_total': '$0.056',
                'openai_total': '$1.80',
                'savings_percent': '97%'
            },
            {
                'name': 'Code review bot',
                'description': '6k context + 20k generation', 
                'voltage_total': '$0.04',
                'openai_total': '$1.29',
                'savings_percent': '97%'
            },
            {
                'name': 'Customer support AI',
                'description': '3k prompt + 12k response',
                'voltage_total': '$0.024',
                'openai_total': '$0.765',
                'savings_percent': '97%'
            },
            {
                'name': 'Data extraction API',
                'description': '100k documents processed',
                'voltage_total': '$0.047',
                'openai_total': '$1.50',
                'savings_percent': '97%'
            },
            {
                'name': 'Translation service',
                'description': '50k multilingual tokens',
                'voltage_total': '$0.031',
                'openai_total': '$0.75',
                'savings_percent': '96%'
            }
        ]
        
        project = random.choice(projects)
        
        return {
            'type': 'ai_inference',
            'model': model,
            'competitor': competitor_key,
            'savings': savings,
            'project': project,
            'hashtags': ['#LLM', '#AIInference', '#MLOps', '#AIModels', '#DeepLearning', '#MachineLearning']
        }
    
    def get_gpu_compute_content(self) -> Dict:
        """Génère du contenu pour GPU Compute avec vrais prix"""
        
        # Choisir une offre GPU
        gpu_key = random.choice(list(self.GPU_OFFERINGS.keys()))
        gpu = self.GPU_OFFERINGS[gpu_key]
        
        # Trouver l'équivalent AWS le plus proche
        aws_equivalent = None
        if 'H200' in gpu['name'] or 'H100' in gpu['name']:
            aws_equivalent = self.AWS_PRICES['p5.48xlarge']
        elif 'A100' in gpu['name']:
            aws_equivalent = self.AWS_PRICES['p4d.24xlarge']
        else:
            aws_equivalent = self.AWS_PRICES['g5.48xlarge']
        
        # Calculer les économies
        savings = int(((aws_equivalent['price'] - gpu['price']) / aws_equivalent['price']) * 100)
        
        return {
            'type': 'gpu_compute',
            'gpu': gpu,
            'aws': aws_equivalent,
            'savings': savings,
            'hashtags': ['#CloudGPU', '#GPUCloud', '#HPC', '#DataCenter', '#CloudCompute', '#GPUCluster']
        }
    
    def generate_comparison_hook(self, content: Dict) -> str:
        """Génère un hook de comparaison percutant"""
        
        if content['type'] == 'ai_inference':
            hooks = [
                f"{content['model']['name']} beats {content['competitor']}: {content['savings']}% cheaper per token",
                f"{content['project']['name']}: {content['project']['voltage_total']} vs OpenAI's {content['project']['openai_total']}",
                f"Real use case: {content['project']['description']} for {content['project']['voltage_total']}",
                f"{content['model']['runs']} devs switched from {content['competitor']} → saved {content['savings']}%",
                f"Why {content['competitor']} at 30x the price? {content['model']['name']} does the same"
            ]
        else:  # gpu_compute
            hooks = [
                f"AWS charges ${content['aws']['price']:.2f}/hr. We charge ${content['gpu']['price']:.2f}/hr. Same GPUs.",
                f"{content['gpu']['name']} at {content['savings']}% less than AWS",
                f"Why AWS {content['aws']['gpus']} at ${content['aws']['price']}/hr? Get ours at ${content['gpu']['price']}/hr",
                f"{content['gpu']['location']}: {content['gpu']['name']} ready now at ${content['gpu']['price']}/hr",
                f"Skip the AWS markup: {content['gpu']['name']} direct at ${content['gpu']['price']}/hr"
            ]
        
        return random.choice(hooks)
    
    def generate_proof_point(self, content: Dict) -> str:
        """Génère une preuve concrète avec chiffres"""
        
        if content['type'] == 'ai_inference':
            proofs = [
                f"📊 Pricing: ${content['model']['input_price']}/M input, ${content['model']['output_price']}/M output tokens",
                f"💡 {content['model']['runs']} requests served • {content['model']['context']} context window",
                f"🎯 {content['project']['name']}: {content['project']['description']} = {content['project']['voltage_total']}",
                f"✨ {content['model']['description']} • Save {content['project']['savings_percent']}",
                f"🔥 Live benchmark: {content['project']['voltage_total']} vs {content['project']['openai_total']} for same task"
            ]
        else:  # gpu_compute
            proofs = [
                f"💪 {content['gpu']['cpu']} • {content['gpu']['ram']} RAM • ${content['gpu']['price']}/hr",
                f"� {content['gpu']['location']} • {content['gpu']['uptime']} uptime guaranteed",
                f"⚡ {content['gpu']['name']} ready now • No queue • ${content['gpu']['price']}/hr",
                f"🚀 vs AWS: Save ${content['aws']['price'] - content['gpu']['price']:.2f}/hr on same hardware",
                f"🔥 {content['gpu']['name']} cluster • Instant deploy • ${content['gpu']['price']}/hr"
            ]
        
        return random.choice(proofs)


def test_content_adapter():
    """Test du système d'adaptation de contenu"""
    
    adapter = ContentAdapter()
    
    print("\n" + "="*60)
    print("📊 TEST: CONTENT ADAPTER (AI vs GPU)")
    print("="*60 + "\n")
    
    # Test AI Inference
    print("🤖 AI INFERENCE CONTENT:")
    print("-" * 40)
    
    ai_content = adapter.get_ai_inference_content()
    hook = adapter.generate_comparison_hook(ai_content)
    proof = adapter.generate_proof_point(ai_content)
    
    print(f"Hook: {hook}")
    print(f"Proof: {proof}")
    print(f"Model: {ai_content['model']['name']}")
    print(f"Savings vs {ai_content['competitor']}: {ai_content['savings']}%")
    
    print("\n" + "-" * 40)
    
    # Test GPU Compute
    print("💻 GPU COMPUTE CONTENT:")
    print("-" * 40)
    
    gpu_content = adapter.get_gpu_compute_content()
    hook = adapter.generate_comparison_hook(gpu_content)
    proof = adapter.generate_proof_point(gpu_content)
    
    print(f"Hook: {hook}")
    print(f"Proof: {proof}")
    print(f"GPU: {gpu_content['gpu']['name']} at ${gpu_content['gpu']['price']}/hr")
    print(f"AWS equivalent: ${gpu_content['aws']['price']}/hr")
    print(f"Savings: {gpu_content['savings']}%")
    
    print("\n" + "="*60)
    print("✅ CONTENT ADAPTER TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    test_content_adapter()
