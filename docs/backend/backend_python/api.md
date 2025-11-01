<!-- # API Reference -->

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
