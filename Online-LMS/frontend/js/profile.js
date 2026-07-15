/* ============================================================
   profile.js — View & update the logged-in user's profile.
   ============================================================ */

async function initProfilePage() {
  const user = requireAuth([]);
  if (!user) return;

  renderSidebar("profile.html");

  try {
    const res = await api.users.profile();
    const profile = res.data;

    document.getElementById("profileName").value = profile.name || "";
    document.getElementById("profileEmail").value = profile.email || "";
    document.getElementById("profilePhone").value = profile.phone || "";
    document.getElementById("profileBio").value = profile.bio || "";
    document.getElementById("profileRoleBadge").textContent = profile.role;

    const avatarEl = document.getElementById("profileAvatarPreview");
    if (profile.avatar) {
      avatarEl.innerHTML = `<img src="${uploadUrl("profile", profile.avatar)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`;
    } else {
      avatarEl.textContent = initials(profile.name);
    }
  } catch (err) {
    showToast(err.message || "Could not load profile", "error");
  }

  document.getElementById("profileForm")?.addEventListener("submit", handleUpdateProfile);
}

async function handleUpdateProfile(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData();
  formData.append("name", form.name.value.trim());
  formData.append("phone", form.phone.value.trim());
  formData.append("bio", form.bio.value.trim());

  const avatarFile = document.getElementById("avatarInput")?.files[0];
  if (avatarFile) formData.append("avatar", avatarFile);

  const submitBtn = form.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving...";

  try {
    const res = await api.users.updateProfile(formData, true);
    const user = getCurrentUser();
    user.name = res.data.name;
    localStorage.setItem("rr_user", JSON.stringify(user));
    showToast("Profile updated successfully", "success");
  } catch (err) {
    showToast(err.message || "Could not update profile", "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Save Changes";
  }
}
