from tavily import TavilyClient


class TavilySearch:
    def __init__(self, api_key) -> None:
        self.__client = TavilyClient(api_key=api_key)

    def search(self, query, search_depth: str = "basic", max_results=10, **kwargs):
        return self.__client.search(
            query, search_depth=search_depth, max_results=max_results, **kwargs
        )

    def get_search_context(
        self,
        query,
        search_depth: str = "basic",
        max_results=10,
        max_token: int = 4000,
        **kwargs
    ):
        return self.__client.get_search_context(
            query,
            search_depth=search_depth,
            max_results=max_results,
            max_token=max_token,
            **kwargs
        )

    def qna_search(self, query, search_depth: str = "basic", max_results=10, **kwargs):
        if isinstance(query, list):
            query = "; ".join(query)
        return self.__client.qna_search(
            query, search_depth=search_depth, max_results=max_results, **kwargs
        )
