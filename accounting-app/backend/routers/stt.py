"""语音识别路由 - 使用 Web Speech API

注意：此路由主要作为备用方案。
推荐使用前端 Web Speech API 进行语音识别，无需后端支持。
此路由可用于未来扩展第三方语音服务。
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from schemas import STTResponse

router = APIRouter(prefix="/api/stt", tags=["语音识别"])


@router.post("", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...)
):
    """语音转文字

    注意：此接口为预留接口，实际使用前端 Web Speech API。

    Args:
        audio: 音频文件

    Returns:
        识别出的文字
    """
    # 读取音频数据
    audio_data = await audio.read()

    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="音频文件为空")

    # TODO: 集成第三方语音识别服务（如讯飞、百度等）
    # 目前返回提示，建议使用前端 Web Speech API

    return STTResponse(
        text="[语音识别服务未配置，请使用浏览器内置语音输入]"
    )


@router.get("/status")
async def stt_status():
    """检查语音识别服务状态

    Returns:
        服务状态
    """
    return {
        "available": False,
        "provider": "web_speech_api",
        "message": "推荐使用浏览器内置 Web Speech API 进行语音识别"
    }
