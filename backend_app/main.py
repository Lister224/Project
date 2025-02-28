from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router
import uvicorn

class MyApp:
    def __init__ (self):
        self.app = FastAPI()
        self.setup_routes()
    
    def setup_routes(self):
        self.app.include_router(router)

    def setup_cors(self):
        origins = [
            "*",
        ]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def get_app(self):
        return self.app

my_app_instance = MyApp()
app = my_app_instance.get_app()

if __name__ == '__main__':
    uvicorn.run(app,host='0.0.0.0', port=8080)