import asyncio
from models.scene import StoryboardRequest, ScenePanel, CharacterDescription, CameraAngle
from services.scene_composition_service import create_scene_service

async def main():
    # Create a storyboard request
    request = StoryboardRequest(
        characters={
            "hero": CharacterDescription(
                name="John",
                age="30",
                gender="male",
                physical_appearance={
                    "build": "athletic",
                    "height": "tall",
                    "hair": "dark brown, short",
                    "eyes": "green"
                },
                clothing={
                    "style": "modern tactical gear",
                    "colors": "dark grey and navy"
                },
                demeanor={
                    "posture": "confident",
                    "movement": "precise and calculated"
                }
            )
        },
        panels=[
            ScenePanel(
                panel_id="scene_1",
                description="A tense moment in a high-tech control room",
                visuals={
                    "lighting": "blue glow from monitors",
                    "atmosphere": "cool and technical",
                    "key_elements": "computer screens, holographic displays"
                },
                camera_angle=CameraAngle.MEDIUM,
                character_focus=["hero"]
            )
        ],
        visual_theme={
            "lighting": "cyberpunk neon",
            "color_palette": "blues and teals with orange accents",
            "mood": "high-tech and dramatic"
        }
    )

    # Create the service
    service = create_scene_service()

    # Generate the storyboard
    async for event in service.generate_storyboard(request):
        if event["type"] == "success":
            print(f"\n✅ Generated scene: {event['data']['scene_id']}")
            print(f"Image URL: {event['data']['image_url']}")
        elif event["type"] == "error":
            print(f"\n❌ Error: {event['message']}")

if __name__ == "__main__":
    asyncio.run(main())