import uvicorn


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=80,
        reload=False,
        app_dir="src",
    )

print("hi")
if __name__ == "__main__":
    main()
