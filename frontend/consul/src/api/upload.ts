import axios from "@/utils/axios";
import type { ApiResponse } from "@/types/interfaces";

// 上传图片响应接口
export interface UploadImageResp {
  url: string;
}

// 上传商品图片
export const uploadImage = (file: File, itemId: number): Promise<ApiResponse<UploadImageResp>> => {
  const formData = new FormData();
  formData.append('file', file);
  
  return axios.post(`/upload/image?itemId=${itemId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};