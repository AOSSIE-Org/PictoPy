<!-- This page is a Swagger UI embed, not prose. The mkdocs swagger-ui-tag plugin requires the <swagger-ui> HTML element; the wrapper div and script scope page-specific CSS. The page title comes from the MkDocs nav config, so no top-level heading is needed here. -->
<!-- markdownlint-disable MD033 MD041 MD010 -->
<!-- # API Reference -->
## Backend API Architecture

PictoPy's Python backend exposes its HTTP API through FastAPI. Requests are routed from the application entry point to the corresponding route module, which interacts with the database and utility layers before returning a Pydantic response model.

```mermaid
flowchart TD
    A[Client] -->|HTTP Request| B[FastAPI Application]
    B --> C[API Router]
    C --> D[Route Handler]
    D --> E[Database Layer]
    D --> F[Utility Layer]
    E --> G[(SQLite Database)]
    D --> H[Pydantic Response Model]
    H -->|JSON Response| A
```
<div class="api-500-wrapper">
	<swagger-ui src="openapi.json"/>
</div>

<!-- Add a small script to mark the page so we can scope header/footer CSS only for this route -->
<script>
	(function () {
		function markApiPage() {
			try {
				document.body.classList.add('api-fixed-500');
			} catch (e) {
				/* ignore */
			}
		}
		if (document.readyState === 'loading') {
			document.addEventListener('DOMContentLoaded', markApiPage);
		} else {
			markApiPage();
		}
	})();
</script>
