# from scrapegraphai.graphs import SmartScraperGraph

# from app.schemas.jobs import JobPosting

# graph_config = {
#     "llm": {
#         "model": "ollama/llama3.1",
#         "model_tokens": 8192,
#         "temperature": 0,
#         "format" : "json"
#     },

#     "verbose": False,
#     "headless": True,

#     # important
#     "browser": {
#         "type": "playwright"
#     }
# }

# def extract_additional_job_info_with_llm(job_link:str) -> JobPosting:
#     smart_scraper_graph = SmartScraperGraph(
#         prompt="""
#             You are extracting data from HTML.

#             IMPORTANT RULES:
#             - Return ONLY valid JSON
#             - Do not include markdown
#             - Do not include explanations
#             - Do not include text before or after JSON
#             - Missing fields must be null
#             - Follow the schema exactly

#         """,
#         source=job_link,
#         config=graph_config,
#         schema=JobPosting
#     )
#     result = smart_scraper_graph.run()
#     return JobPosting.model_validate(result)
