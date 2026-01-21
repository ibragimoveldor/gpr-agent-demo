# gpr_agent.py - Alternative version
from langchain_community.utilities import SQLDatabase
from langchain_anthropic import ChatAnthropic
from langchain_community.agent_toolkits import create_sql_agent
import os

class GPRDefectAgent:
    """AI Agent for querying GPR defect database in natural language"""
    
    def __init__(self, db_path='gpr_defects.db', api_key=None):
        # Initialize database connection
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        
        # Initialize Claude LLM
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key or os.getenv('ANTHROPIC_API_KEY'),
            temperature=0
        )
        
        # Create SQL agent - using string instead of enum
        self.agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="zero-shot-react-description",  # String instead of enum
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def query(self, question: str) -> str:
        """Execute natural language query"""
        try:
            result = self.agent.invoke({"input": question})
            return result['output']
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_schema_info(self) -> str:
        """Return database schema"""
        return self.db.get_table_info()

# Command-line interface
if __name__ == '__main__':
    print("=" * 80)
    print("🔍 GPR Defect Analysis Agent - Interactive Mode")
    print("=" * 80)
    print("\nInitializing agent...")
    
    agent = GPRDefectAgent()
    
    print("\n✅ Agent ready!")
    print("Type your questions (or 'quit' to exit, 'schema' to see database structure)\n")
    
    # Example queries
    examples = [
        "How many defects are in the database?",
        "Show me all critical cavities",
        "What's the average repair cost by defect type?",
        "Which locations have the most defects?"
    ]
    
    print("💡 Example questions:")
    for i, ex in enumerate(examples, 1):
        print(f"   {i}. {ex}")
    print()
    
    while True:
        try:
            query = input("🔍 Your question: ").strip()
            
            if query.lower() == 'quit':
                print("\n👋 Goodbye!")
                break
            elif query.lower() == 'schema':
                print("\n" + "="*80)
                print(agent.get_schema_info())
                print("="*80 + "\n")
                continue
            elif not query:
                continue
            
            print("\n" + "="*80)
            response = agent.query(query)
            print("\n📊 Answer:")
            print(response)
            print("="*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")