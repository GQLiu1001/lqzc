import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { authApi, UserProfile } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Loader2 } from "lucide-react";

interface ProfileEditDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    currentUser: UserProfile;
    onSuccess: () => void;
}

export function ProfileEditDialog({
    open,
    onOpenChange,
    currentUser,
    onSuccess,
}: ProfileEditDialogProps) {
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState<Partial<UserProfile>>({
        nickname: "",
        email: "",
        gender: 1,
        avatar: "",
    });

    useEffect(() => {
        if (open && currentUser) {
            setFormData({
                nickname: currentUser.nickname || "",
                email: currentUser.email || "",
                gender: currentUser.gender || 1,
                avatar: currentUser.avatar || "",
            });
        }
    }, [open, currentUser]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await authApi.updateProfile(formData);
            toast({
                title: "修改成功",
                description: "个人信息已更新",
            });
            onSuccess();
            onOpenChange(false);
        } catch (error) {
            console.error("修改个人信息失败:", error);
            toast({
                title: "修改失败",
                description: error instanceof Error ? error.message : "请稍后重试",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange} modal={false}>
            <DialogContent className="sm:max-w-[425px] bg-white">
                <DialogHeader>
                    <DialogTitle>修改个人信息</DialogTitle>
                    <DialogDescription>
                        在这里修改您的个人资料，完成后点击保存。
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit}>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="nickname" className="text-right">
                                昵称
                            </Label>
                            <Input
                                id="nickname"
                                value={formData.nickname}
                                onChange={(e) =>
                                    setFormData({ ...formData, nickname: e.target.value })
                                }
                                className="col-span-3"
                            />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="email" className="text-right">
                                邮箱
                            </Label>
                            <Input
                                id="email"
                                type="email"
                                value={formData.email}
                                onChange={(e) =>
                                    setFormData({ ...formData, email: e.target.value })
                                }
                                className="col-span-3"
                            />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label className="text-right">性别</Label>
                            <RadioGroup
                                value={formData.gender?.toString()}
                                onValueChange={(val) =>
                                    setFormData({ ...formData, gender: parseInt(val) })
                                }
                                className="flex col-span-3 gap-4"
                            >
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="1" id="male" />
                                    <Label htmlFor="male">男</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="2" id="female" />
                                    <Label htmlFor="female">女</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="0" id="unknown" />
                                    <Label htmlFor="unknown">保密</Label>
                                </div>
                            </RadioGroup>
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="avatar" className="text-right">
                                头像URL
                            </Label>
                            <Input
                                id="avatar"
                                value={formData.avatar}
                                onChange={(e) =>
                                    setFormData({ ...formData, avatar: e.target.value })
                                }
                                className="col-span-3"
                                placeholder="https://..."
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            取消
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            保存修改
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
