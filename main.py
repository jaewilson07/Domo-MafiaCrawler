"""
Web Crawler Application

This is the main entry point for the Web Crawler application.
It provides a Flask-based web interface for configuring and executing
web crawling operations.
"""

# Standard library imports
import os
import logging

# Third-party imports
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# Local application imports
try:
    from routes import crawler as crawler_routes
    CRAWLER_ROUTES_AVAILABLE = True
except ImportError:
    CRAWLER_ROUTES_AVAILABLE = False
    import logging
    logging.warning("crawler_routes module not available. Some functionality will be limited.")
    
    # Create dummy classes and functions
    class CrawlerRouteError(Exception):
        """Placeholder for CrawlerRouteError when crawler_routes is not available."""
        pass
        
    def create_default_browser_config():
        """Placeholder for create_default_browser_config when crawler_routes is not available."""
        return None
        
    def create_default_crawler_config():
        """Placeholder for create_default_crawler_config when crawler_routes is not available."""
        return None
        
    # Create a module-like object with the placeholders
    class _CrawlerRoutes:
        CrawlerRouteError = CrawlerRouteError
        create_default_browser_config = create_default_browser_config
        create_default_crawler_config = create_default_crawler_config
    
    # Use this as a replacement for the imported module
    crawler_routes = _CrawlerRoutes()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "insecure-dev-key")

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)


@app.route("/")
def index():
    """
    Render the home page with the crawler configuration form.
    
    Returns:
        str: Rendered HTML template
    """
    logger.debug("Rendering index page")
    return render_template("index.html")


@app.route("/crawler", methods=["GET", "POST"])
def crawler():
    """
    Handle crawler configuration and execution.
    
    Returns:
        str: Rendered HTML template or JSON response
    """
    if request.method == "POST":
        # Get form data
        url = request.form.get("url")
        session_id = request.form.get("session_id", "default_session")
        
        if not url:
            flash("URL is required", "error")
            return redirect(url_for("index"))
            
        try:
            # Create a browser config with default settings
            browser_config = crawler_routes.create_default_browser_config()
            
            # Set up crawler config based on form data
            crawler_config = crawler_routes.create_default_crawler_config()
            
            # Queue the crawl job (we'd implement a proper job queue in production)
            # For now, just flash a message
            flash(f"Crawling of {url} has been scheduled with session ID: {session_id}", "success")
            
            # In a real app, we'd return a job ID or similar
            return redirect(url_for("index"))
            
        except crawler_routes.CrawlerRouteError as e:
            logger.error(f"Crawler error: {str(e)}")
            flash(f"Crawler error: {str(e)}", "error")
            return redirect(url_for("index"))
            
        except Exception as e:
            logger.exception("Unexpected error")
            flash(f"Unexpected error: {str(e)}", "error")
            return redirect(url_for("index"))
    
    # GET request - show current crawler status or history
    return render_template("crawler.html")


@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    """
    API endpoint for crawling a URL.
    
    Returns:
        dict: JSON response with crawl results or error
    """
    try:
        data = request.json
        url = data.get("url")
        session_id = data.get("session_id", "api_session")
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
            
        # In production, we'd queue this job
        # For now, return a simple response
        return jsonify({
            "status": "queued",
            "message": f"Crawling of {url} has been scheduled",
            "session_id": session_id
        })
        
    except Exception as e:
        logger.exception("API error")
        return jsonify({"error": str(e)}), 500


@app.route("/api/status/<session_id>", methods=["GET"])
def api_status(session_id):
    """
    API endpoint for checking crawl status.
    
    Args:
        session_id (str): The session ID to check
        
    Returns:
        dict: JSON response with crawl status
    """
    # In production, we'd check a job queue or database
    # For now, return a simple response
    return jsonify({
        "status": "pending",
        "session_id": session_id,
        "message": "Crawling in progress"
    })


@app.route("/about")
def about():
    """
    Render the about page.
    
    Returns:
        str: Rendered HTML template
    """
    return render_template("about.html")


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors.
    
    Args:
        error: The error object
        
    Returns:
        tuple: Rendered template and status code
    """
    return render_template("error.html", error=error), 404


@app.errorhandler(500)
def server_error(error):
    """
    Handle 500 errors.
    
    Args:
        error: The error object
        
    Returns:
        tuple: Rendered template and status code
    """
    logger.exception("Server error")
    return render_template("error.html", error=error), 500


if __name__ == "__main__":
    """Run the application when executed directly."""
    # Create templates if they don't exist
    try:
        from utils.files import ensure_template_files_exist
        ensure_template_files_exist()
    except ImportError:
        logger.warning("Could not import ensure_template_files_exist from utils.files")
        # Create basic templates and static directories
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)
        
        # Create minimal template files if needed
        for template_name in ["index.html", "crawler.html", "about.html", "error.html"]:
            template_path = os.path.join('templates', template_name)
            if not os.path.exists(template_path):
                with open(template_path, "w") as f:
                    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Web Crawler Tool - {template_name.replace('.html', '').title()}</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
</head>
<body>
    <h1>Web Crawler Tool</h1>
    <p>Basic placeholder template for {template_name}</p>
</body>
</html>""")
        
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)